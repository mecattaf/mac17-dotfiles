start_all()
machine.wait_for_unit('multi-user.target', timeout=180)
machine.succeed('test -d /sys/firmware/efi')
machine.succeed('test "$(cat /sys/class/dmi/id/sys_vendor)" = QEMU')
machine.succeed('test "$(cat /sys/class/dmi/id/product_name)" = MacBookPro14,3')
machine.succeed('udevadm settle')
machine.succeed(r'''set -eu
 target_link=$(find /dev/disk/by-id -maxdepth 1 -type l -name '*MAC17-TEST-TARGET' | head -n1)
 backup_link=$(find /dev/disk/by-id -maxdepth 1 -type l -name '*MAC17-TEST-BACKUP' | head -n1)
 test -n "$target_link"
 test -n "$backup_link"
 printf '%s\n' "$target_link" > /run/mac17-test-target-link
 printf '%s\n' "$backup_link" > /run/mac17-test-backup-link
 target=$(readlink -f "$target_link")
 backup=$(readlink -f "$backup_link")
 test "$(lsblk -dn -o MODEL "$target" | sed 's/[[:space:]]*$//')" = 'APPLE SSD VM'
 test "$(lsblk -dn -o MODEL "$backup" | sed 's/[[:space:]]*$//')" = 'MAC17 BACKUP'
 sgdisk --clear --new=1:2048:+256M --typecode=1:ef00 --change-name=1:EFI --new=2:0:0 --typecode=2:af0a "$target"
 sgdisk --clear --new=1:0:0 --typecode=1:8300 "$backup"
 partprobe "$target"
 partprobe "$backup"
 udevadm settle
 esp=$(lsblk --tree -J -o PATH,PARTN "$target" | jq -r '.blockdevices[0].children[] | select((.partn|tonumber)==1) | .path')
 backup_part=$(lsblk --tree -J -o PATH,PARTN "$backup" | jq -r '.blockdevices[0].children[] | select((.partn|tonumber)==1) | .path')
 mkfs.vfat "$esp"
 mkfs.ext4 -F "$backup_part"
 mkdir -p /fixture-efi /backup
 mount "$esp" /fixture-efi
 mkdir -p /fixture-efi/EFI/APPLE/EMBEDDEDOS
 printf 'Nonsecret synthetic memboot\n' > /fixture-efi/EFI/APPLE/EMBEDDEDOS/combined.memboot
 printf 'Nonsecret synthetic FDR\n' > /fixture-efi/EFI/APPLE/EMBEDDEDOS/FDRData
 printf '<plist>synthetic</plist>\n' > /fixture-efi/EFI/APPLE/EMBEDDEDOS/version.plist
 sync
 umount /fixture-efi
 mount "$backup_part" /backup
 sfdisk --json "$target" > /run/gpt-before.json
 sha256sum "$esp" | cut -d' ' -f1 > /run/esp-sha-before
 blkid -s PARTUUID -o value "$esp" > /run/esp-partuuid-before
 printf '%s\n' "$target" > /run/mac17-test-target
 printf '%s\n' "$esp" > /run/mac17-test-esp
 sync
''')

if machine.succeed('cat /etc/mac17-test/usb-proof-enabled').strip() == 'yes':
    with subtest('appended USB FAT partition is located from the mounted live ISO'):
        machine.succeed(r'''set -eu
          usb_disk=$(lsblk -dnro PATH,SERIAL | awk '$2 == "MAC17-TEST-USB" {print $1}')
          test -b "$usb_disk"
          test "$(lsblk -dnro TRAN "$usb_disk")" = usb
          iso_part=$(lsblk --tree -J -o PATH,PARTN "$usb_disk" | jq -r '.blockdevices[0].children[] | select((.partn|tonumber)==1) | .path')
          mkdir -p /iso
          mount -o ro "$iso_part" /iso
          bash /etc/mac17-test/mount-usb-backup.sh
          test "$(findmnt -rn -o FSTYPE -T /media/mac17-backup)" = vfat
          test "$(lsblk -dnro PKNAME "$(findmnt -rn -o SOURCE -T /media/mac17-backup)")" = "$(basename "$usb_disk")"
          printf 'Nonsecret guest USB write proof\n' > /media/mac17-backup/guest-proof.txt
          sync -f /media/mac17-backup/guest-proof.txt
          umount /media/mac17-backup
          bash /etc/mac17-test/mount-usb-backup.sh
          grep -Fx 'Nonsecret guest USB write proof' /media/mac17-backup/guest-proof.txt
          umount /media/mac17-backup
          umount /iso
        ''')

with subtest('plan performs zero writes to the selected disk'):
    writes_before = machine.succeed('target=$(cat /run/mac17-test-target); awk \'{print $5 ":" $7}\' "/sys/class/block/$(basename "$target")/stat"').strip()
    machine.succeed('python3 /etc/mac17-test/run-installer.py plan')
    machine.succeed('grep -F "Plan only. Nothing has been changed." /tmp/mac17-plan.log')
    writes_after = machine.succeed('target=$(cat /run/mac17-test-target); awk \'{print $5 ":" $7}\' "/sys/class/block/$(basename "$target")/stat"').strip()
    assert writes_before == writes_after, (writes_before, writes_after)

with subtest('wrong disk model is refused'):
    machine.succeed('python3 /etc/mac17-test/run-installer.py wrong-target')
    machine.succeed('grep -F "does not identify as an internal Apple SSD" /tmp/mac17-wrong-target.log')

with subtest('wrong machine model is refused'):
    machine.succeed('mount --bind /etc/mac17-test/wrong-model /sys/class/dmi/id/product_name')
    machine.succeed('python3 /etc/mac17-test/run-installer.py wrong-model')
    machine.succeed('grep -F "only for MacBookPro14,3" /tmp/mac17-wrong-model.log')
    machine.succeed('umount /sys/class/dmi/id/product_name')

with subtest('incorrect erase phrase leaves target unchanged'):
    machine.succeed('python3 /etc/mac17-test/run-installer.py cancel')
    machine.succeed('grep -F "installation cancelled" /tmp/mac17-cancel.log')
    machine.succeed('target=$(cat /run/mac17-test-target); diff -u /run/gpt-before.json <(sfdisk --json "$target")')
    machine.succeed('esp=$(cat /run/mac17-test-esp); test "$(sha256sum "$esp" | cut -d\' \' -f1)" = "$(cat /run/esp-sha-before)"')

with subtest('mismatching encryption passphrases leave target unchanged'):
    machine.succeed('python3 /etc/mac17-test/run-installer.py passphrase-mismatch')
    machine.succeed('grep -F "disk passphrases do not match" /tmp/mac17-passphrase-mismatch.log')
    machine.succeed('target=$(cat /run/mac17-test-target); diff -u /run/gpt-before.json <(sfdisk --json "$target")')

with subtest('real install from the local prepared closure without networking'):
    machine.succeed('test -z "$(ip route show default)"')
    machine.succeed('python3 /etc/mac17-test/run-installer.py install', timeout=2400)
    machine.succeed('grep -F "Installation finished." /tmp/mac17-install.log')
    machine.succeed('test ! -e /dev/mapper/mac17-root')
    machine.succeed(r'''set -eu
      target=$(cat /run/mac17-test-target)
      esp=$(cat /run/mac17-test-esp)
      test "$(blkid -s PARTUUID -o value "$esp")" = "$(cat /run/esp-partuuid-before)"
      sfdisk --json "$target" > /run/gpt-after.json
      jq -S '.partitiontable.partitions[0] | {start,size,type,uuid}' /run/gpt-before.json > /run/esp-geometry-before.json
      jq -S '.partitiontable.partitions[0] | {start,size,type,uuid}' /run/gpt-after.json > /run/esp-geometry-after.json
      diff -u /run/esp-geometry-before.json /run/esp-geometry-after.json
      mount -o ro "$esp" /fixture-efi
      grep -F 'Nonsecret synthetic memboot' /fixture-efi/EFI/APPLE/EMBEDDEDOS/combined.memboot
      grep -F 'Nonsecret synthetic FDR' /fixture-efi/EFI/APPLE/EMBEDDEDOS/FDRData
      grep -F '<plist>synthetic</plist>' /fixture-efi/EFI/APPLE/EMBEDDEDOS/version.plist
      test -s /fixture-efi/EFI/BOOT/BOOTX64.EFI
      umount /fixture-efi
      test "$(find /backup -name SHA256SUMS | wc -l)" = 3
      while IFS= read -r -d '' sums; do (cd "$(dirname "$sums")"; sha256sum --check SHA256SUMS); done < <(find /backup -name SHA256SUMS -print0)
    ''')
    machine.succeed(r'''set -eu
      target=$(cat /run/mac17-test-target)
      root_part=$(lsblk --tree -J -o PATH,PARTN "$target" | jq -r '.blockdevices[0].children[] | select((.partn|tonumber)==3) | .path')
      printf '%s' 'Synthetic-Disk-Passphrase-Only-2026' | cryptsetup open --key-file=- "$root_part" mac17-proof-root
      mkdir -p /proof-root
      mount /dev/mapper/mac17-proof-root /proof-root
      expected=$(python3 -c 'import json;print(json.load(open("/etc/mac17-test/environment.json"))["targetSystem"])')
      test "$(readlink -f /proof-root/nix/var/nix/profiles/system)" = "$expected"
      test -x "/proof-root$expected/bin/switch-to-configuration"
      nix --extra-experimental-features nix-command path-info --store 'local?root=/proof-root' "$expected"
      test -s /proof-root/etc/nixos/flake.lock
      test -s /proof-root/var/lib/mac17-install/t1-files.sha256
      test -s /proof-root/var/lib/mac17-install/image.json
      grep -E '^tarek:\$[[:alnum:]]+\$' /proof-root/etc/shadow
      umount /proof-root
      cryptsetup close mac17-proof-root
    ''')
