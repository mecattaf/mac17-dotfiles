#!/usr/bin/env python3
"""Native, single-owner free AI launchers. Never accepts or prints credentials."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ZEN_MODELS = ("deepseek-v4.1-flash-free", "glm-5.3-flash-free")
GOOGLE_MODEL = "gemini-3.8-flash-low"
PORTALS = {
    "google": ("Google Antigravity: personal Google Account, weekly free quota", "https://antigravity.google/docs/install/"),
    "google-api": ("Google AI Studio: choose an unbilled Free-tier project", "https://aistudio.google.com/api-keys"),
    "groq": ("Groq: keep the organization on Free", "https://console.groq.com/keys"),
    "openrouter": ("OpenRouter: free variants only; no credits purchase needed", "https://openrouter.ai/settings/keys"),
    "cloudflare": ("Cloudflare Workers AI: Workers Free, 10,000 Neurons/day", "https://dash.cloudflare.com/"),
    "zai": ("Z.ai: only the documented free Flash models", "https://z.ai/manage-apikey/apikey-list"),
    "mistral": ("Mistral: Free web mode; API billing is separate", "https://chat.mistral.ai/"),
    "cohere": ("Cohere: evaluation key, 1,000 calls/month; not production", "https://dashboard.cohere.com/api-keys"),
    "nvidia": ("NVIDIA API Catalog: development/prototyping trial endpoints", "https://build.nvidia.com/"),
    "cerebras": ("Cerebras: optional card-verified $5/30-day trial", "https://cloud.cerebras.ai/"),
    "vercel": ("Vercel: optional card-verified free-credit allowance", "https://vercel.com/ai-gateway"),
}

class Refused(Exception):
    pass

def private_directory(path: Path) -> Path:
    if not path.is_absolute():
        raise Refused("The application state directory must be absolute.")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise Refused("The private application directory is unavailable.")
    path.chmod(0o700)
    return path

def clean_environment():
    env = os.environ.copy()
    for key in tuple(env):
        if (key.startswith(("OPENCODE_", "GEMINI_", "GOOGLE_", "ANTIGRAVITY_", "AGY_", "CLAUDE_", "ANTHROPIC_"))
                or key.endswith(("_API_KEY", "_AUTH_TOKEN", "_ACCESS_TOKEN", "_OAUTH_TOKEN"))
                or key in {"GH_TOKEN", "GITHUB_TOKEN", "CLOUDFLARE_API_TOKEN", "AWS_PROFILE", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"}):
            env.pop(key, None)
    return env

def zen_environment(model):
    if model not in ZEN_MODELS:
        raise Refused("Choose one of the prepared free models; paid models are unavailable through zen.")
    env = clean_environment()
    for variable, fallback in (("XDG_CONFIG_HOME", ".config"), ("XDG_DATA_HOME", ".local/share"),
                               ("XDG_STATE_HOME", ".local/state"), ("XDG_CACHE_HOME", ".cache")):
        original = Path(os.environ.get(variable, str(Path.home() / fallback)))
        env[variable] = str(private_directory(original / "mac17-ai/zen"))
    # Official OpenCode itself uses the public credential when no login exists.
    # It is not an account key and cannot debit a paid account. Never borrow a
    # normal OpenCode login, a DSH plugin, or inherited provider credentials.
    env.update({
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
        "OPENCODE_CONFIG_CONTENT": json.dumps({
            "model": "opencode/" + model,
            "small_model": "opencode/" + model,
            "enabled_providers": ["opencode"],
            "provider": {"opencode": {"whitelist": list(ZEN_MODELS), "options": {"apiKey": "public"}}},
            "autoupdate": False, "share": "disabled", "permission": {"*": "ask"},
        }, separators=(",", ":")),
    })
    return env

def parse_model_listing(output):
    """Parse the pinned native client's model-name + JSON metadata format."""
    decoder = json.JSONDecoder()
    result = {}
    rest = output
    while rest.strip():
        rest = rest.lstrip()
        identifier, separator, rest = rest.partition("\n")
        if not separator or not identifier.startswith("opencode/"):
            raise Refused("The native model catalogue has an unexpected format.")
        try:
            value, end = decoder.raw_decode(rest.lstrip())
        except ValueError:
            raise Refused("The native model catalogue cannot be checked.") from None
        rest = rest.lstrip()[end:]
        result[identifier] = value
    return result

def check_zen_price(binary, environment, model):
    try:
        found = subprocess.run([binary, "models", "opencode", "--verbose", "--pure"],
                               env=environment, capture_output=True, text=True, timeout=25, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise Refused("OpenCode's model catalogue could not be checked. Try agy or retry later.") from None
    if found.returncode:
        raise Refused("OpenCode's free catalogue is unavailable. Try agy or retry later.")
    item = parse_model_listing(found.stdout).get("opencode/" + model, {})
    cost = item.get("cost", {})
    prices = [cost.get("input"), cost.get("output"), cost.get("cache", {}).get("read"), cost.get("cache", {}).get("write")]
    if not all(isinstance(price, (int, float)) and not isinstance(price, bool) and price == 0 for price in prices):
        raise Refused("This model is no longer listed at zero price. No request was sent; choose another prepared free route.")
    if item.get("status") != "active" or not item.get("api", {}).get("url", "").startswith("https://opencode.ai/"):
        raise Refused("The prepared model is unavailable from the official free provider.")

def zen(args):
    parser = argparse.ArgumentParser(prog="zen", description="Official OpenCode with public free models only; limits stop rather than spend money.")
    parser.add_argument("--model", "-m", choices=ZEN_MODELS, default=ZEN_MODELS[0])
    parser.add_argument("--json", action="store_true", help="native JSON events for a one-shot prompt")
    parser.add_argument("prompt", nargs="*")
    options = parser.parse_args(args)
    binary = os.environ["MAC17_OPENCODE"]
    env = zen_environment(options.model)
    check_zen_price(binary, env, options.model)
    argv = [binary]
    if options.prompt:
        argv += ["run", "--pure", "--model", "opencode/" + options.model]
        if options.json:
            argv += ["--format", "json"]
        argv += ["--", " ".join(options.prompt)]
    else:
        argv += ["--pure", "--model", "opencode/" + options.model]
    print("OpenCode free route. A quota or availability error stops here; no paid fallback.\n", file=sys.stderr)
    os.execve(binary, argv, env)

def antigravity(args):
    # These settings are owned by the prepared launcher. Other ordinary native
    # arguments (prompt, resume, mode, effort) retain the vendor's behavior.
    reserved = ("--settings", "--model", "--gemini_dir", "--app_data_dir", "--gemini-dir", "--app-data-dir")
    if any(arg == key or arg.startswith(key + "=") for arg in args for key in reserved):
        raise Refused("The free agy launcher fixes the personal account, Gemini model and credit settings. Use its ordinary prompt, resume and mode options.")
    if args and args[0] in {"update", "install", "remote-control", "mic-serve"}:
        raise Refused("This prepared launcher manages its own package and local account. Use agy for a local assistant session.")
    root = private_directory(Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "mac17-ai/antigravity")
    env = clean_environment()
    env.update({"AGY_CLI_DISABLE_AUTO_UPDATE": "true", "ANTIGRAVITY_GEMINI_DIR": str(root), "ANTIGRAVITY_APP_DATA_DIR": "antigravity-cli"})
    binary = os.environ["MAC17_ANTIGRAVITY"]
    # Preserve desktop D-Bus: the single local owner can use Secret Service.
    # The private vendor fallback token directory is inside encrypted /home.
    argv = [binary, "--gemini_dir", str(root), "--app_data_dir", "antigravity-cli",
            "--model", GOOGLE_MODEL, "--settings", '{"useG1Credits":false}', *args]
    os.execve(binary, argv, env)

def open_portal(identifier):
    if identifier not in PORTALS:
        raise Refused("Unknown provider. Run mac17-ai providers for the supported names.")
    return subprocess.call([os.environ.get("MAC17_BROWSER", "/run/current-system/sw/bin/mac17-browser"), PORTALS[identifier][1]])

def setup():
    print("Your free AI setup\n\n1  Google Antigravity — sign in with your own personal Google Account\n2  OpenCode — public free models, if anonymous quota is available\n3  More free API accounts — enter keys later in DSH Settings → Models\n\nNo payment details or subscriptions are needed for options 1 and 2.\nGoogle credit fallback is disabled. Quota exhaustion never switches providers.\n")
    choice = input("Choose 1, 2 or 3 (Enter for Google): ").strip() or "1"
    if choice == "1":
        print("\nChoose your own personal Google Account in Chrome. Ask a small first question,\nthen return to Imagine after you receive a reply. /usage shows quota.\n")
        return antigravity([])
    if choice == "2":
        print("\nIf OpenCode reports a free limit, stop and use Google instead.\n")
        return zen([])
    if choice == "3":
        providers()
        print("\nOpen a portal with: mac17-ai open NAME\nThen use DSH: Settings → Models → Add model provider.\nAPI keys go into the native write-only credential field, never this terminal,\nGit, shell profiles, or the onboarding progress file. See /etc/mac17/free-ai.md.\n")
        return 0
    raise Refused("Choose 1, 2 or 3; setup can be reopened any time.")

def providers():
    for identifier, (description, _) in PORTALS.items():
        print(f"{identifier:12} {description}")

def main(args):
    os.umask(0o077)
    try:
        if not args or args[0] == "setup":
            return setup()
        if args[0] == "zen":
            return zen(args[1:])
        if args[0] == "agy":
            return antigravity(args[1:])
        if args[0] == "providers":
            providers(); return 0
        if len(args) == 2 and args[0] == "open":
            return open_portal(args[1])
        if args == ["status", "--json"]:
            print(json.dumps({"schema": 1, "clientsInstalled": all(Path(os.environ.get(k, "")).is_file() for k in ("MAC17_OPENCODE", "MAC17_ANTIGRAVITY")), "credentialsChecked": False, "primary": "personal-google-oauth", "creditFallback": False, "anonymousZenGuaranteed": False}))
            return 0
        raise Refused("Use mac17-ai setup, providers, open NAME, or status --json; zen and agy launch the native clients.")
    except (Refused, EOFError) as error:
        print("mac17-ai: " + str(error), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
