#!/usr/bin/env python3
"""Type only into the disposable guest's explicitly selected QMP socket."""
import json
from pathlib import Path
import socket
import sys
import time

path = Path(sys.argv[1]).resolve()
assert str(path).startswith('/tmp/mac17-iso-proof/') and path.name == 'qmp.sock'
client = socket.socket(socket.AF_UNIX)
client.connect(str(path))
stream = client.makefile('rwb', buffering=0)
json.loads(stream.readline())

def execute(command):
    stream.write(json.dumps(command).encode() + b'\n')
    while True:
        result = json.loads(stream.readline())
        if 'return' in result:
            return result
        if 'error' in result:
            raise RuntimeError(result)

execute({'execute': 'qmp_capabilities'})
punctuation = {' ': 'spc', '-': 'minus', '.': 'dot', '/': 'slash', '@': 'shift-2', ':': 'shift-semicolon', '_': 'shift-minus', '\n': 'ret'}
for char in sys.argv[2]:
    if char in punctuation:
        key = punctuation[char]
    elif char.isascii() and (char.islower() or char.isdigit()):
        key = char
    elif char.isascii() and char.isupper():
        key = 'shift-' + char.lower()
    else:
        raise ValueError(char)
    execute({'execute': 'human-monitor-command', 'arguments': {'command-line': 'sendkey ' + key + ' 20'}})
    time.sleep(0.06)
client.close()
