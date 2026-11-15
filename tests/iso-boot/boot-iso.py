#!/usr/bin/env python3
"""EFI USB boot probe. Run only under runtime-test --allow-kvm on compute.

Only an immutable Nix-store image is attached, with QEMU snapshot=on. No host
block device, shared store, host home, network interface or credentials enter
the guest. stdin accepts JSON commands for this process's QMP/serial sockets.
"""
import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import struct
import sys
import threading
import time
import zlib

parser = argparse.ArgumentParser()
parser.add_argument('--iso', required=True)
parser.add_argument('--work', required=True)
args = parser.parse_args()
image = Path(args.iso).resolve()
work = Path(args.work).resolve()
assert str(image).startswith('/nix/store/') and image.is_file()
assert str(work).startswith('/tmp/mac17-iso-proof/')
work.mkdir(parents=True, exist_ok=True)
os.umask(0o077)
qemu = '/nix/store/aag02nvd7725yrvqz5s4shwznj97zxk4-qemu-for-vm-tests-11.1.2/bin/qemu-system-x86_64'
ovmf = Path('/nix/store/yycwiw0kn80r3r3haw224ar1gp9cvjzb-OVMF-202608-fd/FV')
shutil.copyfile(ovmf / 'OVMF_VARS.fd', work / 'nvram.fd')
qmp_path = work / 'qmp.sock'
serial_path = work / 'serial.sock'
for path in (qmp_path, serial_path):
    if path.exists():
        path.unlink()
command = [qemu, '-machine', 'q35,accel=kvm', '-cpu', 'host', '-smp', '4',
           '-m', '8192', '-nic', 'none', '-no-reboot', '-display', 'none',
           '-drive', f'if=pflash,format=raw,readonly=on,file={ovmf}/OVMF_CODE.fd',
           '-drive', f'if=pflash,format=raw,file={work}/nvram.fd',
           '-device', 'qemu-xhci,id=mac17usb',
           '-drive', f'if=none,id=mac17iso,file={image},format=raw,snapshot=on',
           '-device', 'usb-storage,bus=mac17usb.0,drive=mac17iso,bootindex=1,serial=MAC17-TEST-USB',
           '-smbios', 'type=1,manufacturer=QEMU,product=MacBookPro14,,3',
           '-qmp', f'unix:{qmp_path},server=on,wait=off',
           '-serial', f'unix:{serial_path},server=on,wait=off', '-monitor', 'none']
(work / 'qemu-command.json').write_text(json.dumps(command, indent=2) + '\n')
qemu_log = (work / 'qemu.log').open('wb')
process = subprocess.Popen(command, stdout=qemu_log, stderr=subprocess.STDOUT)
serial = None
serial_buffer = bytearray()
serial_lock = threading.Lock()


def connect(path):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError((work / 'qemu.log').read_text())
        try:
            client = socket.socket(socket.AF_UNIX)
            client.connect(str(path))
            return client
        except (FileNotFoundError, ConnectionRefusedError):
            time.sleep(0.1)
    raise TimeoutError(str(path))


def qmp(execute, arguments=None):
    client = connect(qmp_path)
    stream = client.makefile('rwb', buffering=0)
    json.loads(stream.readline())
    for request in ({'execute': 'qmp_capabilities'}, {'execute': execute, 'arguments': arguments or {}}):
        stream.write(json.dumps(request).encode() + b'\n')
        while True:
            answer = json.loads(stream.readline())
            if 'return' in answer:
                break
            if 'error' in answer:
                raise RuntimeError(answer)
    client.close()
    return answer


def screenshot(filename):
    # The realized headless QEMU lacks libpng. Preserve its exact PPM and encode
    # the same pixels using the Python standard library, without a new build.
    ppm = filename.with_suffix('.ppm')
    qmp('screendump', {'filename': str(ppm)})
    magic, dimensions, maximum, pixels = ppm.read_bytes().split(b'\n', 3)
    assert magic == b'P6' and maximum == b'255'
    width, height = map(int, dimensions.split())
    assert len(pixels) == width * height * 3
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', binascii.crc32(kind + data) & 0xffffffff)
    scanlines = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b'')
    filename.write_bytes(png)
    return {'screenshot': str(filename), 'original_ppm': str(ppm)}


def read_serial():
    with (work / 'serial.log').open('wb', buffering=0) as log:
        while True:
            data = serial.recv(65536)
            if not data:
                break
            log.write(data)
            with serial_lock:
                serial_buffer.extend(data)


try:
    serial = connect(serial_path)
    threading.Thread(target=read_serial, daemon=True).start()
    print(json.dumps({'state': 'running', 'pid': process.pid, 'work': str(work)}), flush=True)
    for line in sys.stdin:
        with (work / 'commands.jsonl').open('a') as command_log:
            command_log.write(line)
        request = json.loads(line)
        action = request['action']
        if action == 'quit':
            break
        if action == 'freeze_menu':
            for _ in range(8):
                qmp('human-monitor-command', {'command-line': 'sendkey down 30'})
                time.sleep(1)
            qmp('human-monitor-command', {'command-line': 'sendkey home 30'})
            answer = screenshot(work / 'efi-menu.png')
        elif action == 'key':
            answer = qmp('human-monitor-command', {'command-line': 'sendkey ' + request['key'] + ' 30'})
        elif action == 'capture':
            filename = work / request.get('name', 'screen.png')
            assert filename.parent == work and filename.suffix == '.png'
            answer = screenshot(filename)
        elif action == 'serial':
            serial.sendall(request['text'].encode())
            answer = {'sent_bytes': len(request['text'].encode())}
        elif action == 'guest_script':
            script = Path(request['path']).read_bytes()
            encoded = base64.b64encode(script).decode()
            serial.sendall(('echo ' + encoded + ' | base64 -d | sudo -n bash\r').encode())
            answer = {'sent_script_bytes': len(script)}
        elif action == 'status':
            with serial_lock:
                tail = bytes(serial_buffer[-6000:]).decode(errors='replace')
            answer = {'qemu': qmp('query-status'), 'serial_tail': tail}
        else:
            raise ValueError(action)
        print(json.dumps({'action': action, 'result': answer}), flush=True)
finally:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    if serial is not None:
        serial.close()
    qemu_log.close()
    print(json.dumps({'state': 'stopped', 'exit': process.returncode}), flush=True)
