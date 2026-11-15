#!/usr/bin/env python3
"""NAS/DSH-side read-only API. Explicit desktop registry, fixed remote helper."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
from protocol import MAX_BYTES, ProtocolError, validate_reply, workspace_query

def ssh_command(record,desktop,expected=None):
    prefix=["ssh"]
    if "sshConfig" in record:
        config=record["sshConfig"]
        if not isinstance(config,str) or not config.startswith("/") or any(c in config for c in "\r\n\0"):
            raise ProtocolError("invalid explicit SSH config")
        info=Path(config).lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:
            raise ProtocolError("explicit SSH config must be an owned regular mode0600 file")
        prefix += ["-F",config]
    peer=ipaddress.ip_address(record["tailnetIp"])
    if peer not in ipaddress.ip_network("100.64.0.0/10"):
        raise ProtocolError("only explicit Tailscale IPv4 transport is supported")
    for key in ("sshAlias","hostKeyAlias"):
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*",record[key]):raise ProtocolError("invalid trusted SSH alias")
    helper=record["helper"]
    if not isinstance(helper,str) or not helper.startswith("/") or any(c in helper for c in "\r\n\0"):
        raise ProtocolError("explicit installed helper path required")
    remote=[helper,desktop]
    if expected:remote += ["--expect-epoch",expected[0],"--expect-revision",str(expected[1])]
    return prefix+["-T","-oBatchMode=yes","-oStrictHostKeyChecking=yes","-oConnectTimeout=5","-oConnectionAttempts=1","-oClearAllForwardings=yes","-oForwardAgent=no","-oControlMaster=no","-oControlPath=none","-oControlPersist=no",f"-oHostName={peer}",f"-oHostKeyAlias={record['hostKeyAlias']}",record["sshAlias"],shlex.join(remote)]

def query(registry,desktop,workspace=None,expected=None):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}",desktop) or desktop not in registry.get("desktops",{}):
        raise ProtocolError("explicit known desktop required")
    result=subprocess.run(ssh_command(registry["desktops"][desktop],desktop,expected),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=False)
    if len(result.stdout)>MAX_BYTES:raise ProtocolError("oversized remote reply")
    if result.returncode not in (0,3):raise ProtocolError("desktop transport unavailable; no fallback")
    try:envelope=json.loads(result.stdout)
    except ValueError as error:raise ProtocolError("invalid remote envelope") from error
    reply=validate_reply(result.stdout,envelope.get("requestId"),desktop)
    if not isinstance(reply.get("requestId"),str) or not re.fullmatch(r"[a-f0-9]{32}",reply["requestId"]):raise ProtocolError("invalid request identity")
    if expected and reply["ok"] and (reply["epoch"],reply["revision"])!=expected:raise ProtocolError("stale reply")
    return workspace_query(reply,workspace) if workspace is not None and reply["ok"] else reply

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry",required=True,type=Path)
    parser.add_argument("--desktop",required=True)
    parser.add_argument("--workspace")
    parser.add_argument("--expect-epoch")
    parser.add_argument("--expect-revision",type=int)
    args=parser.parse_args()
    if (args.expect_epoch is None)!=(args.expect_revision is None):parser.error("both expected epoch and revision are required")
    try:
        expected=(args.expect_epoch,args.expect_revision) if args.expect_epoch else None
        result=query(json.loads(args.registry.read_text()),args.desktop,args.workspace,expected)
        print(json.dumps(result,indent=2))
        return 0 if result["ok"] else 3
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print(json.dumps({"ok":False,"error":{"code":"unavailable","message":str(error) if isinstance(error,ProtocolError) else "snapshot query failed"}}))
        return 2

if __name__=="__main__":sys.exit(main())
