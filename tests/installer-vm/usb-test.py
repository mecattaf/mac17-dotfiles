from datetime import timedelta

start_all()
machine.wait_for_unit('multi-user.target', timeout=timedelta(seconds=180))
machine.succeed('test -d /sys/firmware/efi')
machine.succeed('test "$(cat /sys/class/dmi/id/sys_vendor)" = QEMU')
machine.succeed('test "$(cat /sys/class/dmi/id/product_name)" = MacBookPro14,3')
machine.succeed('udevadm settle')
machine.succeed('test "$(cat /etc/mac17-test/usb-proof-enabled)" = yes')
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
