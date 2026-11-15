import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("free_ai", Path(__file__).resolve().parents[1] / "scripts/mac17-ai.py")
ai = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(ai)

def listing(price=0, missing_cache=False):
    cost = {"input": price, "output": 0, "cache": {"read": 0, "write": 0}}
    if missing_cache: del cost["cache"]["write"]
    return "opencode/" + ai.ZEN_MODELS[0] + "\n" + json.dumps({"status": "active", "api": {"url": "https://opencode.ai/inference/openai/v1"}, "cost": cost}) + "\n"

class FreeAiTests(unittest.TestCase):
    def test_paid_model_is_rejected_before_state_creation(self):
        with self.assertRaises(ai.Refused): ai.zen_environment("paid-model")

    def test_inherited_credentials_are_removed_but_desktop_keyring_is_preserved(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "SECRET", "OPENCODE_API_KEY": "SECRET", "ANTHROPIC_API_KEY": "SECRET", "GOOGLE_APPLICATION_CREDENTIALS": "/private", "DBUS_SESSION_BUS_ADDRESS": "session-bus"}):
            env = ai.clean_environment()
        self.assertNotIn("GEMINI_API_KEY", env); self.assertNotIn("OPENCODE_API_KEY", env)
        self.assertNotIn("ANTHROPIC_API_KEY", env); self.assertNotIn("GOOGLE_APPLICATION_CREDENTIALS", env)
        self.assertEqual(env["DBUS_SESSION_BUS_ADDRESS"], "session-bus")

    def test_only_explicit_zero_cost_metadata_passes(self):
        with patch.object(ai.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, listing(), "")):
            ai.check_zen_price("native", {}, ai.ZEN_MODELS[0])
        for response in (listing(price=0.01), listing(missing_cache=True)):
            with patch.object(ai.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, response, "")):
                with self.assertRaises(ai.Refused): ai.check_zen_price("native", {}, ai.ZEN_MODELS[0])

    def test_catalogue_failure_is_closed_and_does_not_repeat_or_fallback(self):
        with patch.object(ai.subprocess, "run", side_effect=subprocess.TimeoutExpired("native", 25)) as run:
            with self.assertRaises(ai.Refused): ai.check_zen_price("native", {}, ai.ZEN_MODELS[0])
        self.assertEqual(run.call_count, 1)

    def test_unknown_catalogue_format_is_refused(self):
        for value in ("unexpected output", "opencode/free\nnot-json"):
            with self.assertRaises(ai.Refused): ai.parse_model_listing(value)

    def test_zen_state_is_private_and_fixed_public_identity(self):
        with tempfile.TemporaryDirectory() as root:
            envs = {key: root + "/" + key for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME")}
            with patch.dict(os.environ, envs): env = ai.zen_environment(ai.ZEN_MODELS[0])
            config = json.loads(env["OPENCODE_CONFIG_CONTENT"])
            self.assertEqual(config["provider"]["opencode"]["options"]["apiKey"], "public")
            self.assertEqual(config["enabled_providers"], ["opencode"])
            self.assertEqual(Path(env["XDG_DATA_HOME"]).stat().st_mode & 0o777, 0o700)

    def test_credit_and_account_overrides_are_refused(self):
        for args in (["--settings", '{"useG1Credits":true}'], ["--settings=paid.json"], ["--model", "third-party"], ["--gemini_dir", "/other"]):
            with self.assertRaises(ai.Refused): ai.antigravity(args)

    def test_google_native_launch_has_no_credit_fallback_or_inherited_key(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"XDG_DATA_HOME": root, "MAC17_ANTIGRAVITY": "/native/agy", "GEMINI_API_KEY": "SECRET"}):
                with patch.object(ai.os, "execve") as execute:
                    ai.antigravity(["--mode", "plan"])
            _, argv, env = execute.call_args.args
            self.assertEqual(argv[argv.index("--settings") + 1], '{"useG1Credits":false}')
            self.assertEqual(argv[argv.index("--model") + 1], ai.GOOGLE_MODEL)
            self.assertNotIn("GEMINI_API_KEY", env)
            self.assertEqual(Path(root, "mac17-ai/antigravity").stat().st_mode & 0o777, 0o700)

    def test_portal_does_not_accept_arbitrary_url(self):
        with patch.object(ai.subprocess, "call") as execute:
            with self.assertRaises(ai.Refused): ai.open_portal("https://other.invalid")
        execute.assert_not_called()

if __name__ == "__main__": unittest.main()
