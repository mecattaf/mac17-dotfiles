#!/usr/bin/env python3
"""Fixed host adapter for Imagine onboarding; stdin JSON, coarse JSON replies.

Never accepts shell text, paths, URLs, credentials, or executable names from the
UI. Native CLIs own authentication and their terminal streams. This process
returns status categories only. No network or login action runs at import time.
"""
from __future__ import annotations
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tempfile

MAX_REQUEST = 4096
MAX_STATE = 32768
MAX_RESPONSE = 15000
STATUSES = {"pending", "complete", "deferred"}
HOST_ACTIONS = {"network.open", "tour.launcher", "tour.workspaces"}
NATIVE_ACTIONS = {
    "chrome.open-profile", "keyring.open", "tailscale.login", "tailscale.open-users",
    "github.login", "claude.login", "dsh.first-session", "cloudflare.login",
    "hardware.open-checks", "tour.terminal", "tour.touchbar", "design.open-workspace",
}
TASKS = {"tailscale.login", "github.login", "claude.login", "dsh.first-session", "cloudflare.login", "hardware.open-checks"}

class Refused(Exception):
    pass

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def command(name):
    configured = os.environ.get("MAC17_" + name.upper().replace("-", "_"))
    return configured or name

def private_env():
    result = os.environ.copy()
    # Verify the browser/CLI account, not an inherited automation override.
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_API_KEY",
                "CLOUDFLARE_EMAIL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"):
        result.pop(key, None)
    result["GH_PROMPT_DISABLED"] = "1"
    return result

def run(argv, timeout=12):
    try:
        return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=timeout, env=private_env(), check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None

def root():
    base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
    if not base.is_absolute():
        raise Refused("The state directory must be absolute.")
    result = base / "imagine/onboarding"
    result.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = result.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise Refused("The private setup directory is unavailable.")
    result.chmod(0o700)
    return result

@contextlib.contextmanager
def state_lock():
    path = root() / "state.lock"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)

def manifest():
    path = Path(os.environ.get("MAC17_JOURNEY", "/etc/mac17/onboarding-journey.json"))
    value = json.loads(path.read_text())
    if value.get("schemaVersion") != 1 or not isinstance(value.get("steps"), list):
        raise Refused("The setup instructions are unavailable.")
    steps = value["steps"]
    ids = [s.get("id") for s in steps]
    if len(ids) != len(set(ids)) or not all(isinstance(i, str) for i in ids):
        raise Refused("The setup instructions contain invalid steps.")
    for step in steps:
        if step.get("action") not in HOST_ACTIONS | NATIVE_ACTIONS | {"onboarding.finish"}:
            raise Refused("The setup instructions contain an unsupported action.")
    return value

def state():
    path = root() / "state.json"
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return {"schema": 1, "visibility": "open", "steps": {}, "leases": {}}
    with os.fdopen(fd) as source:
        if os.fstat(source.fileno()).st_size > MAX_STATE:
            raise Refused("Saved setup progress is too large; it has been kept.")
        try:
            value = json.load(source)
        except (ValueError, OSError):
            raise Refused("Saved setup progress cannot be read; it has been kept.") from None
    if value.get("schema") != 1 or not isinstance(value.get("steps"), dict):
        raise Refused("Saved setup progress has an unsupported format; it has been kept.")
    value.setdefault("leases", {})
    return value

def save(value):
    value["updatedAt"] = now()
    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False) + "\n"
    if len(encoded.encode()) > MAX_STATE:
        raise Refused("Saved setup progress is too large.")
    fd, temporary = tempfile.mkstemp(prefix=".state-", dir=root())
    try:
        with os.fdopen(fd, "w") as target:
            target.write(encoded)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, root() / "state.json")
        parent = os.open(root(), os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)

def step_for(identifier):
    return next((s for s in manifest()["steps"] if s["id"] == identifier), None)

def probe(identifier):
    result = {"state": "manual", "message": "Confirm this step after trying it."}
    if identifier == "network":
        found = run([command("nmcli"), "--get-values", "STATE,CONNECTIVITY", "general"])
        if found is None or found.returncode:
            return {"state": "unavailable", "message": "NetworkManager status is unavailable."}
        text = found.stdout.lower()
        if "portal" in text:
            return {"state": "portal", "message": "This network needs a browser sign-in. Open Quick settings."}
        if text.startswith("connected"):
            return {"state": "ready", "message": "Connected. Chrome can check Internet access."}
        return {"state": "offline", "message": "Choose a network in Quick settings."}
    if identifier == "tailscale":
        found = run([command("tailscale"), "status", "--json"])
        try:
            value = json.loads(found.stdout) if found is not None else {}
        except ValueError:
            value = {}
        if value.get("BackendState") == "Running" and value.get("Self", {}).get("Online"):
            return {"state": "ready", "message": "Tailscale is connected. Check that this is your own account."}
        return {"state": "signed-out", "message": "Sign in to your own Tailscale account."}
    if identifier == "github":
        found = run([command("gh"), "api", "user", "--jq", ".login"])
        if found is None:
            return {"state": "unavailable", "message": "GitHub could not be checked. Check the connection and retry."}
        if found.returncode:
            return {"state": "signed-out", "message": "GitHub sign-in needs attention."}
        login = found.stdout.strip()
        expected = step_for("github").get("completion", {}).get("expectedLogin")
        if not login or len(login) > 100 or any(not (c.isalnum() or c == "-") for c in login):
            return {"state": "unavailable", "message": "GitHub returned an unexpected account identity."}
        return {"state": "ready" if login == expected else "wrong-account", "message":
                f"Signed in as {login}." if login == expected else f"Signed in as {login}; use {expected}."}
    if identifier == "claude":
        found = run([command("claude"), "auth", "status"])
        try:
            value = json.loads(found.stdout) if found is not None else {}
        except ValueError:
            return {"state": "unavailable", "message": "This Claude version needs its native account status check."}
        if value.get("loggedIn") is True:
            return {"state": "ready", "message": "Claude Code reports a signed-in account."}
        return {"state": "signed-out", "message": "Sign in with your own Claude account."}
    if identifier == "cloudflare":
        found = run([command("wrangler"), "whoami"], 20)
        if found is None:
            return {"state": "unavailable", "message": "Cloudflare could not be checked. Retry when connected."}
        text = (found.stdout + found.stderr).lower()
        if not found.returncode and "you are logged in" in text:
            return {"state": "ready", "message": "Wrangler reports a signed-in Cloudflare account."}
        return {"state": "signed-out", "message": "Authorize Wrangler with your own Cloudflare account."}
    if identifier == "chrome":
        return {"state": "manual", "message": "Use Chrome's profile button. A Google website login alone does not sign in the browser profile."}
    if identifier == "manager":
        return {"state": "manual", "message": "Send Tom an Admin invitation from Tailscale Users. Record acceptance here; Tom verifies remote access separately."}
    return result

def keyring_ready():
    found = run([command("gdbus"), "call", "--session", "--dest", "org.freedesktop.secrets",
                 "--object-path", "/org/freedesktop/secrets/collection/login", "--method",
                 "org.freedesktop.DBus.Properties.Get", "org.freedesktop.Secret.Collection", "Locked"])
    return found is not None and found.returncode == 0 and found.stdout.strip() == "(<false>,)"

def process_stamp(pid):
    try:
        # PID plus kernel start tick prevents accepting a reused PID as a lease.
        fields = Path(f"/proc/{int(pid)}/stat").read_text().rsplit(")", 1)[1].split()
        return fields[19]
    except (OSError, ValueError, IndexError):
        return None

def lease_running(lease):
    if not isinstance(lease, dict):
        return False
    if lease.get("pid") and lease.get("start"):
        return process_stamp(lease["pid"]) == lease["start"]
    try:
        return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(lease["at"])).total_seconds() < 20
    except (KeyError, ValueError, TypeError):
        return False

def project(value):
    steps = []
    for step in manifest()["steps"]:
        row = {k: step[k] for k in ("id", "title", "body", "action", "required", "requires") if k in step}
        row["completion"] = {k: v for k, v in step.get("completion", {}).items() if k in {"kind", "text", "acknowledgement"}}
        stored = value["steps"].get(step["id"], {})
        row["status"] = stored.get("status", "pending")
        row["evidence"] = stored.get("evidence")
        row["running"] = lease_running(value["leases"].get(step["action"]))
        steps.append(row)
    return {"schema": 1, "visibility": value.get("visibility", "open"), "currentStep": value.get("currentStep"), "steps": steps}

def dependencies_ready(step, value):
    return all(value["steps"].get(i, {}).get("status") == "complete" for i in step.get("requires", []))

def record(identifier, status):
    step = step_for(identifier)
    if step is None or status not in STATUSES:
        raise Refused("Unknown setup step or progress state.")
    if status == "complete":
        if not dependencies_ready(step, state()):
            raise Refused("Finish the earlier required step first.")
        if step.get("completion", {}).get("kind") == "probe" and probe(identifier)["state"] != "ready":
            raise Refused("The account or connection is not ready yet. Check it and retry.")
    with state_lock():
        value = state()
        evidence = "observed" if step.get("completion", {}).get("kind") == "probe" else "acknowledged"
        value["steps"][identifier] = {"status": status, "evidence": evidence if status == "complete" else None, "at": now()}
        value["currentStep"] = identifier
        save(value)
        return project(value)

def launch(action):
    if action not in NATIVE_ACTIONS:
        raise Refused("That setup action is not supported by the host.")
    if action != "keyring.open":
        step = next((s for s in manifest()["steps"] if s["action"] == action), None)
        if step is None or not dependencies_ready(step, state()):
            raise Refused("Finish the earlier setup step before starting this action.")
    if action in {"chrome.open-profile", "tailscale.open-users"} and not keyring_ready():
        raise Refused("The login keyring is not ready. Open Passwords and Keys to create or unlock the login keyring, then retry Chrome.")
    if action in TASKS:
        with state_lock():
            value = state()
            if lease_running(value["leases"].get(action)):
                return {"launched": False, "running": True, "message": "This sign-in is already open in Kitty."}
            nonce = secrets.token_hex(16)
            value["leases"][action] = {"nonce": nonce, "at": now()}
            value["visibility"] = "minimized"
            save(value)
        argv = [command("kitty"), "--class", "imagine-setup", "--title", "Set up your computer", "--hold",
                sys.executable, str(Path(__file__).resolve()), "--worker", action, nonce]
    elif action == "chrome.open-profile":
        argv = [command("browser")]
    elif action == "tailscale.open-users":
        argv = [command("browser"), "https://login.tailscale.com/admin/users"]
    elif action == "keyring.open":
        argv = [command("seahorse")]
    elif action in {"tour.terminal", "tour.touchbar"}:
        argv = [command("kitty")]
    else:
        argv = [command("nautilus"), str(Path.home() / "Projects")]
    try:
        subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         env=private_env(), start_new_session=True, close_fds=True)
    except OSError:
        if action in TASKS:
            with state_lock():
                value = state()
                if value["leases"].get(action, {}).get("nonce") == nonce:
                    value["leases"].pop(action, None)
                    save(value)
        raise Refused("The native application could not start. Check its installation.") from None
    return {"launched": True, "running": action in TASKS, "message": "Continue in the native application, then reopen setup."}

def worker(action, nonce):
    if action not in TASKS or len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
        return 2
    with state_lock():
        value = state()
        if value["leases"].get(action, {}).get("nonce") != nonce:
            return 2
        value["leases"][action].update(pid=os.getpid(), start=process_stamp(os.getpid()))
        save(value)
    environment = private_env()
    environment.pop("GH_PROMPT_DISABLED", None)
    args = {
        "tailscale.login": [command("sudo"), command("tailscale"), "up", "--operator", "tarek"],
        "github.login": [command("gh"), "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web"],
        "claude.login": [command("claude"), "auth", "login"],
        "cloudflare.login": [command("wrangler"), "login"],
    }
    exit_code = 1
    try:
        if action == "cloudflare.login":
            help_result = run([command("wrangler"), "login", "--help"])
            if help_result and "--use-keyring" in help_result.stdout:
                args[action].append("--use-keyring")
                environment["CLOUDFLARE_AUTH_USE_KEYRING"] = "true"
        if action == "dsh.first-session":
            project_dir = Path.home() / "Projects"
            project_dir.mkdir(exist_ok=True)
            check = subprocess.run([command("dshd"), "get", "welcome"], capture_output=True, env=environment, check=False)
            if check.returncode:
                subprocess.run([command("dshd"), "run", "--name", "welcome", "--", "web"], cwd=project_dir, env=environment, check=True)
            exit_code = subprocess.run([command("dshd"), "attach", "welcome"], cwd=project_dir, env=environment, check=False).returncode
        elif action == "hardware.open-checks":
            print("Check the keyboard and trackpad, connect to Wi-Fi, then test the camera and quiet audio.\nUse your normal desktop apps. Sleep/wake needs a separate check.\n")
            subprocess.run([command("nmcli"), "device", "status"], env=environment, check=False)
            subprocess.run([command("lsusb")], env=environment, check=False)
            print("\nNo hardware check is marked complete by this report. Confirm after trying the device.")
            exit_code = 0
        else:
            exit_code = subprocess.run(args[action], env=environment, check=False).returncode
            if exit_code == 0 and action == "github.login":
                subprocess.run([command("gh"), "auth", "setup-git"], env=environment, check=False)
        print("\nReturn to Imagine setup to check this step and continue." if exit_code == 0 else "\nThis action did not finish. Your progress is kept; retry from Imagine setup.")
    except (OSError, subprocess.SubprocessError):
        print("\nThe native account tool could not finish. Retry from Imagine setup.", file=sys.stderr)
    finally:
        with state_lock():
            value = state()
            if value["leases"].get(action, {}).get("nonce") == nonce:
                value["leases"].pop(action, None)
                value.setdefault("attempts", {})[action] = {"at": now(), "result": "finished" if exit_code == 0 else "failed"}
                save(value)
    return exit_code

def respond(request):
    if not isinstance(request, dict):
        raise Refused("Expected a setup request.")
    op = request.get("op")
    allowed = {"op"} | ({"step", "status"} if op == "record" else {"step"} if op in {"probe", "select"} else {"action"} if op == "launch" else {"visibility"} if op == "visibility" else set())
    if set(request) - allowed:
        raise Refused("Unexpected setup request fields.")
    if op == "state":
        return project(state())
    if op == "select":
        if step_for(request.get("step")) is None:
            raise Refused("Unknown setup step.")
        with state_lock():
            value = state()
            value["currentStep"] = request["step"]
            save(value)
            return project(value)
    if op == "probe":
        if step_for(request.get("step")) is None:
            raise Refused("Unknown setup step.")
        return probe(request["step"])
    if op == "record":
        return record(request.get("step"), request.get("status"))
    if op == "launch":
        return launch(request.get("action"))
    if op == "visibility":
        if request.get("visibility") not in {"open", "minimized"}:
            raise Refused("Unknown setup visibility.")
        with state_lock():
            value = state()
            value["visibility"] = request["visibility"]
            save(value)
            return project(value)
    if op == "finish":
        with state_lock():
            value = state()
            missing = [s for s in manifest()["steps"] if s.get("required") and s["id"] != "finish" and value["steps"].get(s["id"], {}).get("status") != "complete"]
            if missing:
                raise Refused("Some required steps are still unfinished. You can minimize setup and return later.")
            value["steps"]["finish"] = {"status": "complete", "evidence": "acknowledged", "at": now()}
            value["visibility"] = "complete"
            save(value)
            return project(value)
    raise Refused("Unknown setup operation.")

def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        return worker(sys.argv[2], sys.argv[3])
    if len(sys.argv) != 1:
        return 2
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            raise Refused("Setup request is too large.")
        response = {"ok": True, "result": respond(json.loads(raw))}
    except Refused as error:
        response = {"ok": False, "error": str(error)}
    except (OSError, ValueError, TypeError, KeyError):
        response = {"ok": False, "error": "Setup could not read its private state. Existing progress has been kept."}
    encoded = json.dumps(response, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode()) > MAX_RESPONSE:
        encoded = '{"ok":false,"error":"Setup response exceeded its size limit."}'
    print(encoded)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
