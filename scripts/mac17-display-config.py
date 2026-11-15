#!/usr/bin/env python3
"""Keep a writable Domicile config and learn this Mac's first Retina profile.

The immutable Nix wrapper selects the validator. Display observations come from
the host entry's read-only public SDK observer, never an inferred EDID hash or
logical-size multiplication. No credentials or application contents are read.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time

LIMIT = 1024 * 1024
MISSING = object()
PROFILE_NAME = "mac17-retina"


class ConfigError(Exception):
    pass


def private_directory(path: Path) -> None:
    if path.is_symlink():
        raise ConfigError("configuration directory must not be a symlink")
    path.mkdir(parents=True, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ConfigError("configuration directory must belong to this user")
    path.chmod(0o700)


def read_json(path: Path, *, optional=False, immutable=False, migrate_link=False):
    try:
        info = path.lstat()
    except FileNotFoundError:
        if optional:
            return MISSING
        raise ConfigError("required configuration is absent")
    if stat.S_ISLNK(info.st_mode):
        target = path.resolve(strict=True)
        if not migrate_link or not str(target).startswith("/nix/store/"):
            raise ConfigError("configuration symlink is not a managed store file")
        return read_json(target, immutable=True)
    if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
        raise ConfigError("configuration must be a bounded regular file")
    # A runtime-test user namespace represents root-owned store files with an
    # unmapped UID. Trust their canonical immutable store location/permissions,
    # not a particular numeric owner; user preferences still require this UID.
    managed_store = immutable and str(path.resolve(strict=True)).startswith("/nix/store/") and not info.st_mode & 0o222
    if info.st_uid != os.getuid() and not managed_store:
        raise ConfigError("configuration file belongs to another user")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as source:
        now = os.fstat(source.fileno())
        if (now.st_dev, now.st_ino) != (info.st_dev, info.st_ino):
            raise ConfigError("configuration changed while reading")
        data = source.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ConfigError("configuration exceeds its size limit")
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ConfigError("configuration must be a JSON object")
    return result


def clone(value):
    return MISSING if value is MISSING else copy.deepcopy(value)


def merge_preferences(old, current, new):
    """Three-way merge: changed user values/deletions win over a new base."""
    if current == old:
        return clone(new)
    if isinstance(current, dict) and isinstance(new, dict) and (old is MISSING or isinstance(old, dict)):
        previous = {} if old is MISSING else old
        result = {}
        for key in previous.keys() | current.keys() | new.keys():
            value = merge_preferences(previous.get(key, MISSING), current.get(key, MISSING), new.get(key, MISSING))
            if value is not MISSING:
                result[key] = value
        return result
    return clone(current)


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def atomic_json(path: Path, value) -> bool:
    data = encoded(value)
    if path.exists() and not path.is_symlink() and path.read_bytes() == data:
        if stat.S_IMODE(path.stat().st_mode) != 0o600:
            path.chmod(0o600)
        return False
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


class Store:
    def __init__(self, config: Path, state: Path, validator: str):
        self.config, self.state, self.validator = config, state, validator
        private_directory(config.parent)
        private_directory(state)

    def lock(self):
        path = self.state / "lock"
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            os.close(fd)
            raise ConfigError("configuration lock must belong to this user")
        deadline = time.monotonic() + 10
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return os.fdopen(fd, "r+")
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    os.close(fd)
                    raise ConfigError("configuration is busy")
                time.sleep(0.05)

    def validate(self, value):
        fd, temporary = tempfile.mkstemp(prefix=".validate.", suffix=".json", dir=self.config.parent)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(encoded(value))
            result = subprocess.run([self.validator, "check-config", temporary],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=False)
            if result.returncode != 0:
                raise ConfigError("Domicile rejected the proposed configuration")
        finally:
            os.unlink(temporary)

    def stage(self, base_path: Path):
        with self.lock():
            base = read_json(base_path, immutable=True)
            if not isinstance(base.get("shell"), str) or not base["shell"].startswith("/nix/store/"):
                raise ConfigError("prepared base must name its immutable prebuilt shell")
            previous = read_json(self.state / "base.json", optional=True)
            current = read_json(self.config, optional=True, migrate_link=True)
            if current is MISSING:
                merged = clone(base)
            else:
                merged = merge_preferences(previous, current, base)
            # A user's preferences survive; the selected generation always
            # supplies the current prebuilt shell rather than a stale path.
            merged["shell"] = base["shell"]
            self.validate(merged)
            changed = atomic_json(self.config, merged)
            atomic_json(self.state / "base.json", base)
            return {"status": "staged", "changed": changed}

    def observe(self, observation):
        displays = decode_observation(observation)
        with self.lock():
            current = read_json(self.config)
            learned = read_json(self.state / "retina.json", optional=True)
            if learned is not MISSING:
                # Never reset a later choice made in native Displays Settings.
                return {"status": learned.get("status", "preserved"), "changed": False}
            output = current.get("output", {})
            if not isinstance(output, dict):
                raise ConfigError("output configuration must be an object")
            if output.get("profiles") or output.get("displays"):
                atomic_json(self.state / "retina.json", {"schema": 1, "status": "user-configured"})
                return {"status": "user-configured", "changed": False}
            # Initial learning is deliberately laptop-only. A dock/external
            # display is not guessed to be this Mac's built-in Retina panel.
            if len(displays) != 1:
                return {"status": "waiting-for-laptop-only", "changed": False}
            display = displays[0]
            if (display["modeWidth"], display["modeHeight"]) != (2880, 1800) or display["transform"] != "normal":
                return {"status": "waiting-for-retina-mode", "changed": False}
            profile = {"name": PROFILE_NAME, "displays": [{
                "display": display["name"], "mode": [2880, 1800], "scale": 2,
            }]}
            proposed = clone(current)
            proposed["output"] = {**output, "profiles": [profile]}
            self.validate(proposed)
            changed = atomic_json(self.config, proposed)
            atomic_json(self.state / "retina.json", {
                "schema": 1, "status": "learned", "display": display["name"],
                "mode": [2880, 1800], "initialScale": 2,
            })
            return {"status": "learned", "changed": changed}


def decode_observation(value):
    if not isinstance(value, dict) or set(value) != {"schema", "locked", "displays"} or type(value["schema"]) is not int or value["schema"] != 1 or value["locked"] is not False:
        raise ConfigError("display observation is unavailable or locked")
    displays = value["displays"]
    fields = {"name", "modeWidth", "modeHeight", "width", "height", "scale", "transform"}
    if not isinstance(displays, list) or len(displays) > 32:
        raise ConfigError("display observation exceeds its limit")
    names = set()
    for display in displays:
        if not isinstance(display, dict) or set(display) != fields:
            raise ConfigError("display observation has unknown fields")
        name = display["name"]
        if not isinstance(name, str) or not 1 <= len(name) <= 256 or any(ord(c) < 32 or ord(c) == 127 for c in name) or name in names:
            raise ConfigError("display observation has invalid identities")
        names.add(name)
        for key in ["modeWidth", "modeHeight", "width", "height", "scale"]:
            number = display[key]
            if type(number) not in [int, float] or not math.isfinite(number) or number < 0 or number > 65536:
                raise ConfigError("display observation has invalid geometry")
        if display["scale"] <= 0 or display["transform"] not in ["normal", "rotate-90", "rotate-180", "rotate-270"]:
            raise ConfigError("display observation has invalid scale or transform")
    return displays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/domicile/domicile.json")
    parser.add_argument("--state-dir", type=Path, default=Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "mac17-display-config")
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser("stage")
    stage.add_argument("--base", type=Path, required=True)
    sub.add_parser("observe")
    args = parser.parse_args()
    try:
        validator = os.environ.get("MAC17_DOMICILE_BINARY")
        if not validator or not os.path.isabs(validator):
            raise ConfigError("the pinned Domicile validator is not configured")
        store = Store(args.config, args.state_dir, validator)
        if args.command == "stage":
            result = store.stage(args.base)
        else:
            payload = sys.stdin.read(16385)
            if len(payload) > 16384:
                raise ConfigError("display observation exceeds its size limit")
            result = store.observe(json.loads(payload))
        print(json.dumps({"ok": True, "result": result}, separators=(",", ":")))
        return 0
    except (OSError, ValueError, TypeError, KeyError, ConfigError, subprocess.SubprocessError) as error:
        message = str(error) if isinstance(error, ConfigError) else "display configuration could not be updated"
        print(json.dumps({"ok": False, "error": message}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
