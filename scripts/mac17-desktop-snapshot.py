#!/usr/bin/env python3
"""Read the configured same-UID Imagine desktop through the existing protocol.

No caller selects a binary, socket, config path or command. Inter-device SSH
transport remains in the separately bundled upstream query; it is not weakened
or used for this same-laptop route.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

# Set by the immutable Nix wrapper, not by model arguments.
PAYLOAD = Path(os.environ.get("DSH_DOMICILE_PAYLOAD", str(Path(__file__).resolve().parent)))
sys.path.insert(0, str(PAYLOAD))
from client_helper import request as native_request
from protocol import ProtocolError, workspace_query

EXPECTED_FIELDS = {"desktopId", "runtimeDirectory", "domicileBinary", "imagineSource", "sdkSource", "replyRoot"}
EPOCH = re.compile(r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}")


def read_config():
    uid = int(os.environ["DSH_DOMICILE_RUNTIME_UID"])
    if os.getuid() != uid or os.geteuid() != uid:
        raise ProtocolError("snapshot requires the configured desktop user")
    directory = Path.home() / ".config/dsh-domicile"
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700:
        raise ProtocolError("snapshot config directory must be owned mode0700")
    fd = os.open(directory / "client.json", os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 8192:
            raise ProtocolError("snapshot config must be an owned regular mode0600 file")
        config = json.load(source)
    if set(config) != EXPECTED_FIELDS:
        raise ProtocolError("snapshot config fields do not match the installed client")
    expected = {
        "desktopId": os.environ["DSH_DOMICILE_DESKTOP_ID"],
        "runtimeDirectory": f"/run/user/{uid}",
        "domicileBinary": os.environ["DSH_DOMICILE_BINARY"],
        "imagineSource": os.environ["DSH_DOMICILE_IMAGINE_SOURCE"],
        "sdkSource": os.environ["DSH_DOMICILE_SDK_SOURCE"],
        "replyRoot": ".local/state/dsh-domicile/replies",
    }
    if config != expected:
        raise ProtocolError("snapshot config differs from the installed client identity")
    if not re.fullmatch(r"[a-f0-9]{40}", config["sdkSource"]):
        raise ProtocolError("invalid installed SDK identity")
    return config


def query(desktop, workspace=None, expected=None):
    config = read_config()
    if desktop != config["desktopId"]:
        raise ProtocolError("explicit desktop does not match the installed client")
    if workspace is not None and not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", workspace):
        raise ProtocolError("invalid workspace identity")
    if expected is not None and (not EPOCH.fullmatch(expected[0]) or type(expected[1]) is not int or not 1 <= expected[1] <= 9007199254740991):
        raise ProtocolError("invalid expected snapshot identity")
    # The reviewed helper checks private runtime/reply directories, native socket
    # peer UID, nonce, deadlines, O_NOFOLLOW and the full privacy/schema contract.
    result = native_request(config, desktop, expected)
    if result["source"]["sdk"] != config["sdkSource"] or result["source"]["imagine"] != config["imagineSource"]:
        raise ProtocolError("running snapshot source differs from the configured client")
    if expected and result["ok"] and (result["epoch"], result["revision"]) != expected:
        raise ProtocolError("running snapshot is stale")
    if workspace is not None and result["ok"]:
        if not any(item["name"] == workspace for item in result["snapshot"]["workspaces"]):
            raise ProtocolError("workspace not found")
        return workspace_query(result, workspace)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop", required=True, choices=[os.environ.get("DSH_DOMICILE_DESKTOP_ID", "tarek-mac17")])
    parser.add_argument("--workspace")
    parser.add_argument("--expect-epoch")
    parser.add_argument("--expect-revision", type=int)
    args = parser.parse_args()
    if (args.expect_epoch is None) != (args.expect_revision is None):
        parser.error("both expected epoch and revision are required")
    try:
        expected = (args.expect_epoch, args.expect_revision) if args.expect_epoch else None
        result = query(args.desktop, args.workspace, expected)
        print(json.dumps(result, separators=(",", ":")))
        return 0 if result["ok"] else 3
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        # Fixed local transport codes only: no socket paths, command stderr,
        # native errors or cached previous snapshots enter an agent response.
        if isinstance(error, OSError):
            print(f"dsh-domicile local transport or cleanup failed: errno={error.errno}", file=sys.stderr)
        code = "workspace-not-found" if isinstance(error, ProtocolError) and str(error) == "workspace not found" else "unavailable"
        print(json.dumps({"ok": False, "desktopId": args.desktop, "error": {"code": code}}, separators=(",", ":")))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
