#!/usr/bin/env python3
"""Native package smoke test; run through runtime-test on the build host.

Uses a fresh DSH home/cwd, an allowlisted environment and a loopback-only server.
It makes no model request, signs into no account and starts no systemd instance.
"""
import argparse
import http.cookiejar
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsh", required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix="mac17-dsh-smoke-") as directory:
        scratch = Path(directory)
        dsh_home = scratch / "dsh"
        environment = {
            "PATH": "/run/current-system/sw/bin",
            "DSH_HOME": str(dsh_home),
            "DSH_PERMISSION_MODE": "danger-full-access",
            "DSH_TELEMETRY_DISABLED": "1",
            "XDG_CONFIG_HOME": str(scratch / "config"),
            "XDG_CACHE_HOME": str(scratch / "cache"),
            "XDG_DATA_HOME": str(scratch / "data"),
            "XDG_STATE_HOME": str(scratch / "state"),
        }
        if "XDG_RUNTIME_DIR" in os.environ:
            environment["XDG_RUNTIME_DIR"] = os.environ["XDG_RUNTIME_DIR"]
        version = subprocess.check_output(
            [str(args.dsh), "--version"], env=environment, cwd=scratch,
            text=True, timeout=20,
        ).strip()
        log_path = scratch / "startup.log"
        with log_path.open("w") as log:
            process = subprocess.Popen(
                [str(args.dsh), "web", "--no-open", "--host", "127.0.0.1", "--port", "0"],
                env=environment, cwd=scratch, stdout=log, stderr=log,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 50
                ready_url = None
                while time.monotonic() < deadline and process.poll() is None:
                    content = log_path.read_text()
                    match = re.search(r"dsh web: (https?://127\.0\.0\.1:\d+/[^\s]*)", content)
                    if match:
                        ready_url = match.group(1)
                        break
                    time.sleep(0.1)
                if ready_url is None:
                    # Never dump logs that might contain authenticated URLs.
                    raise AssertionError(f"native DSH did not become ready; exit={process.poll()}")
                # DSH redeems its launch token, sets a cookie and redirects to
                # the UI. Exercise that browser handshake without logging it.
                browser = urllib.request.build_opener(
                    urllib.request.ProxyHandler({}),
                    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                )
                with browser.open(ready_url, timeout=10) as response:
                    assert response.status == 200, response.status
                    assert b"<html" in response.read().lower()
                profile = dsh_home / "profiles" / "web"
                assert (profile / "package.json").is_file()
                assert not profile.is_symlink()
                assert not (profile / "cordis.patch.yml").is_symlink()
                assert process.poll() is None, "native DSH exited after becoming ready"
                result = {
                    "version": version,
                    "webReady": True,
                    "loopbackHTTP": 200,
                    "nativeWritableProfile": True,
                    "modelRequests": 0,
                }
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                        raise AssertionError("native DSH did not shut down after SIGTERM")
                assert process.returncode in (0, -signal.SIGTERM), (
                    f"native DSH ended unexpectedly: {process.returncode}"
                )
        result["cleanShutdown"] = True
        print(json.dumps(result))


if __name__ == "__main__":
    main()
