"""Preference migration and physical-mode learning, without a live desktop."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/mac17-display-config.py"
spec = importlib.util.spec_from_file_location("display_config", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def observation(**changes):
    display = {"name": "drm-actual-observed-panel", "modeWidth": 2880,
               "modeHeight": 1800, "width": 2880, "height": 1800,
               "scale": 1, "transform": "normal"}
    display.update(changes)
    return {"schema": 1, "locked": False, "displays": [display]}


class DisplayConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mac17-display-test-")
        self.root = Path(self.temp.name)
        self.config = self.root / "config/domicile.json"
        self.state = self.root / "state"
        self.base = self.root / "prepared.json"
        self.store = module.Store(self.config, self.state, "/immutable/domicile")
        self.validate = patch.object(self.store, "validate").start()
        self.addCleanup(patch.stopall)
        self.addCleanup(self.temp.cleanup)
        self.defaults = {"shell": "/nix/store/initial/shell.js", "theme": {"mode": "dark"},
                         "input": {"touchpad": {"tap": True, "natural_scroll": True}}}
        self.write_base(self.defaults)

    def write_base(self, value):
        self.base.write_text(json.dumps(value))

    def read(self):
        return json.loads(self.config.read_text())

    def write_current(self, value):
        self.config.write_text(json.dumps(value))

    def test_stage_creates_private_real_config_and_stable_repeat(self):
        self.assertTrue(self.store.stage(self.base)["changed"])
        self.assertFalse(self.config.is_symlink())
        self.assertEqual(self.read(), self.defaults)
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.config.parent.stat().st_mode), 0o700)
        before = self.config.stat().st_mtime_ns
        attributes = self.config.stat().st_ctime_ns
        self.assertFalse(self.store.stage(self.base)["changed"])
        self.assertEqual(before, self.config.stat().st_mtime_ns)
        self.assertEqual(attributes, self.config.stat().st_ctime_ns)

    def test_upgrade_merges_new_defaults_and_preserves_user_changes(self):
        self.store.stage(self.base)
        current = self.read()
        current["theme"]["mode"] = "light"
        current["input"]["touchpad"]["tap"] = False
        del current["input"]["touchpad"]["natural_scroll"]
        current["output"] = {"profiles": [{"name": "my-layout", "displays": []}]}
        current["shell"] = "/user/old-shell"
        self.write_current(current)
        newer = copy.deepcopy(self.defaults)
        newer["shell"] = "/nix/store/new-generation/shell.js"
        newer["input"]["touchpad"]["disable_while_typing"] = "libinput"
        newer["terminal"] = ["kitty"]
        self.write_base(newer)
        self.store.stage(self.base)
        actual = self.read()
        self.assertEqual(actual["shell"], newer["shell"])
        self.assertEqual(actual["theme"], current["theme"])
        self.assertEqual(actual["output"], current["output"])
        self.assertFalse(actual["input"]["touchpad"]["tap"])
        self.assertNotIn("natural_scroll", actual["input"]["touchpad"])
        self.assertEqual(actual["input"]["touchpad"]["disable_while_typing"], "libinput")
        self.assertEqual(actual["terminal"], ["kitty"])

    def test_untouched_defaults_follow_new_generation_and_removed_keys(self):
        self.store.stage(self.base)
        newer = copy.deepcopy(self.defaults)
        newer["theme"]["mode"] = "light"
        del newer["input"]["touchpad"]["tap"]
        self.write_base(newer)
        self.store.stage(self.base)
        self.assertEqual(self.read(), newer)

    def test_validation_failure_leaves_config_and_old_base_unchanged(self):
        self.store.stage(self.base)
        before = self.config.read_bytes()
        old_base = (self.state / "base.json").read_bytes()
        self.write_base({**self.defaults, "shell": "/nix/store/rejected/shell.js"})
        self.validate.side_effect = module.ConfigError("rejected")
        with self.assertRaises(module.ConfigError):
            self.store.stage(self.base)
        self.assertEqual(before, self.config.read_bytes())
        self.assertEqual(old_base, (self.state / "base.json").read_bytes())

    def test_foreign_symlink_is_not_followed_or_replaced(self):
        target = self.root / "someone-elses-config"
        target.write_text("do not overwrite")
        self.config.symlink_to(target)
        with self.assertRaises(module.ConfigError):
            self.store.stage(self.base)
        self.assertTrue(self.config.is_symlink())
        self.assertEqual(target.read_text(), "do not overwrite")

    def test_observed_native_retina_mode_learns_actual_name_at_two(self):
        self.store.stage(self.base)
        result = self.store.observe(observation())
        self.assertEqual(result, {"status": "learned", "changed": True})
        placement = self.read()["output"]["profiles"][0]["displays"]
        self.assertEqual(placement, [{"display": "drm-actual-observed-panel", "mode": [2880, 1800], "scale": 2}])
        self.assertEqual(json.loads((self.state / "retina.json").read_text())["initialScale"], 2)

    def test_learned_profile_survives_upgrade_without_reapplying_user_scale(self):
        self.store.stage(self.base)
        self.store.observe(observation())
        current = self.read()
        current["output"]["profiles"][0]["displays"][0]["scale"] = 1.5
        self.write_current(current)
        self.write_base({**self.defaults, "shell": "/nix/store/next/shell.js"})
        self.store.stage(self.base)
        before = self.config.stat().st_mtime_ns
        self.assertFalse(self.store.observe(observation(width=1920, height=1200, scale=2))["changed"])
        self.assertEqual(self.read()["output"], current["output"])
        self.assertEqual(before, self.config.stat().st_mtime_ns)

    def test_unknown_physical_mode_is_never_inferred_from_logical_size(self):
        self.store.stage(self.base)
        before = self.config.read_bytes()
        result = self.store.observe(observation(modeWidth=0, modeHeight=0, scale=2))
        self.assertEqual(result["status"], "waiting-for-retina-mode")
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.state / "retina.json").exists())

    def test_dock_and_rotated_panel_defer_until_laptop_only(self):
        self.store.stage(self.base)
        both = observation()
        both["displays"].append({**both["displays"][0], "name": "external", "modeWidth": 1920, "modeHeight": 1080})
        self.assertEqual(self.store.observe(both)["status"], "waiting-for-laptop-only")
        self.assertEqual(self.store.observe(observation(transform="rotate-90"))["status"], "waiting-for-retina-mode")
        self.assertEqual(self.store.observe(observation())["status"], "learned")

    def test_existing_user_output_is_preserved_even_without_learning_state(self):
        self.store.stage(self.base)
        current = self.read()
        current["output"] = {"profiles": [{"name": "chosen", "displays": [{"display": "mine", "scale": 1.5}]}]}
        self.write_current(current)
        self.assertEqual(self.store.observe(observation())["status"], "user-configured")
        self.assertEqual(current, self.read())

    def test_invalid_or_locked_observation_cannot_mutate_config(self):
        self.store.stage(self.base)
        before = self.config.read_bytes()
        examples = [{**observation(), "locked": True}, {**observation(), "schema": True},
                    {**observation(), "unexpected": "not accepted"}, observation(name="invalid\nname"),
                    observation(modeWidth=float("nan")), observation(scale=0), observation(width=True)]
        for value in examples:
            with self.subTest(value=value):
                with self.assertRaises(module.ConfigError):
                    self.store.observe(value)
        self.assertEqual(before, self.config.read_bytes())


class ValidatorTests(unittest.TestCase):
    def test_validator_receives_actual_private_candidate_and_removes_only_that_file(self):
        with tempfile.TemporaryDirectory(prefix="mac17-validator-test-") as temporary:
            root = Path(temporary)
            store = module.Store(root / "config/domicile.json", root / "state", "/nix/store/pinned/bin/domicile")
            sentinel = root / "config/unrelated"
            sentinel.write_text("keep")
            def inspect(command, **options):
                self.assertEqual(command[:2], [store.validator, "check-config"])
                candidate = Path(command[2])
                self.assertEqual(json.loads(candidate.read_text()), {"shell": "/prepared"})
                self.assertEqual(stat.S_IMODE(candidate.stat().st_mode), 0o600)
                return subprocess.CompletedProcess(command, 0)
            with patch.object(module.subprocess, "run", side_effect=inspect):
                store.validate({"shell": "/prepared"})
            self.assertEqual(sorted(p.name for p in sentinel.parent.iterdir()), ["unrelated"])


@unittest.skipUnless(os.environ.get("MAC17_TEST_DISPLAY_HELPER") and os.environ.get("MAC17_TEST_CHECKED_CONFIG"),
                     "requires the packaged helper and a checked prebuilt base")
class PackagedValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mac17-display-packaged-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "config/domicile.json"
        self.state = self.root / "state"
        self.helper = os.environ["MAC17_TEST_DISPLAY_HELPER"]
        self.base = Path(os.environ["MAC17_TEST_CHECKED_CONFIG"])

    def cli(self, *args, payload=None, success=True):
        completed = subprocess.run([self.helper, "--config", str(self.config), "--state-dir", str(self.state), *args],
                                   input=None if payload is None else json.dumps(payload),
                                   text=True, capture_output=True, timeout=20)
        response = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0 if success else 1, completed.stderr + completed.stdout)
        self.assertIs(response["ok"], success)
        return response

    def test_real_validator_accepts_prebuilt_shell_and_learned_retina_profile(self):
        self.cli("stage", "--base", str(self.base))
        result = self.cli("observe", payload=observation())["result"]
        self.assertEqual(result["status"], "learned")
        self.assertTrue(result["changed"])
        before = self.config.stat().st_mtime_ns
        self.assertFalse(self.cli("observe", payload=observation(width=1440, height=900, scale=2))["result"]["changed"])
        self.assertFalse(self.cli("stage", "--base", str(self.base))["result"]["changed"])
        self.assertEqual(before, self.config.stat().st_mtime_ns)

    def test_managed_store_symlink_becomes_writable_file(self):
        self.config.parent.mkdir()
        self.config.symlink_to(self.base)
        self.cli("stage", "--base", str(self.base))
        self.assertFalse(self.config.is_symlink())
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)
        self.assertEqual(json.loads(self.config.read_text()), json.loads(self.base.read_text()))

    def test_real_validator_rejection_preserves_current_file(self):
        self.cli("stage", "--base", str(self.base))
        before = self.config.read_bytes()
        invalid = json.loads(self.base.read_text())
        invalid["output"] = {"profiles": [{"name": "invalid", "displays": [{"display": "panel", "scale": 0}]}]}
        candidate = self.root / "bad-base.json"
        candidate.write_text(json.dumps(invalid))
        self.cli("stage", "--base", str(candidate), success=False)
        self.assertEqual(before, self.config.read_bytes())


if __name__ == "__main__":
    unittest.main()
