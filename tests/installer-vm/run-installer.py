"""Guest-only PTY driver for the immutable installer source.

The QEMU manufacturer and synthetic disk serial checks prevent this fixture
from being used against a physical Mac or an unrecognized disk.
"""
import json
import os
from pathlib import Path
import sys

import pexpect

assert Path('/sys/class/dmi/id/sys_vendor').read_text().strip() == 'QEMU'
configuration = json.loads(Path('/etc/mac17-test/environment.json').read_text())
scenario = sys.argv[1]
disk = Path('/run/mac17-test-target-link').read_text().strip()
if scenario == 'wrong-target':
    disk = Path('/run/mac17-test-backup-link').read_text().strip()
assert 'MAC17-TEST-' in disk
arguments = ['/etc/mac17-test/install-prepared.sh', '--disk', disk]
if scenario in ('cancel', 'passphrase-mismatch', 'install'):
    arguments += ['--install', '--backup-dir', '/backup']
environment = os.environ.copy()
environment.update({
    'MAC17_TARGET_SYSTEM': configuration['targetSystem'],
    'MAC17_TARGET_SOURCE': configuration['targetSource'],
    'MAC17_SOURCE_REVISION': configuration['sourceRevision'],
})
with open('/tmp/mac17-' + scenario + '.log', 'w') as log:
    child = pexpect.spawn('/run/current-system/sw/bin/bash', arguments,
                          env=environment, encoding='utf-8', timeout=1800)
    child.logfile_read = log
    try:
        if scenario in ('cancel', 'passphrase-mismatch', 'install'):
            child.expect_exact('Type INSTALL MAC17 to continue: ')
            child.sendline('cancel' if scenario == 'cancel' else 'INSTALL MAC17')
        if scenario in ('passphrase-mismatch', 'install'):
            child.expect_exact('Choose the disk-unlock passphrase: ')
            child.sendline('Synthetic-Disk-Passphrase-Only-2026')
            child.expect_exact('Repeat the disk-unlock passphrase: ')
            child.sendline('mismatch' if scenario == 'passphrase-mismatch' else 'Synthetic-Disk-Passphrase-Only-2026')
        if scenario == 'install':
            child.expect_exact('New password:')
            child.sendline('Synthetic-Login-Passphrase-Only-2026')
            child.expect_exact('Retype new password:')
            child.sendline('Synthetic-Login-Passphrase-Only-2026')
        child.expect(pexpect.EOF)
        child.close()
    except BaseException:
        log.flush()
        print(Path(log.name).read_text()[-12000:])
        raise

status = child.exitstatus if child.exitstatus is not None else 128 + (child.signalstatus or 0)
print('scenario', scenario, 'exit', status)
if scenario in ('plan', 'install'):
    assert status == 0, Path('/tmp/mac17-' + scenario + '.log').read_text()[-6000:]
else:
    assert status != 0, 'installer unexpectedly accepted a refusal scenario'
