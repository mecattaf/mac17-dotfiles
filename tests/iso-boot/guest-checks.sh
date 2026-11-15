set -euo pipefail
printf '\nMAC17_ISO_GUEST_CHECKS_BEGIN\n'
test -d /sys/firmware/efi
test "$(cat /sys/class/dmi/id/sys_vendor)" = QEMU
test "$(cat /sys/class/dmi/id/product_name)" = MacBookPro14,3
test "$(uname -r)" = 7.3.4
test -z "$(ip route show default)"
manifest=/etc/mac17/install/image.json
jq -e '.targetSystem == "/nix/store/a5m9aw920zsa929d5g266sfqfbwlsa97-nixos-system-tarek-mac17-26.11.20261113.d5cc683" and .targetSource == "/nix/store/0iqm5pk8axwkm28mkh48w4m8nqw6i71w-source" and .hardwareModel == "MacBookPro14,3"' "$manifest"
cat "$manifest"
target=$(jq -r '.targetSystem' "$manifest")
source=$(jq -r '.targetSource' "$manifest")
test -x "$target/bin/switch-to-configuration"
test -s "$source/flake.lock"
sha256sum "$source/flake.lock"
nix-store -qR "$target" > /tmp/mac17-prepared-closure
while IFS= read -r item; do test -e "$item" || test -L "$item"; done < /tmp/mac17-prepared-closure
printf 'Prepared closure paths: '
wc -l < /tmp/mac17-prepared-closure
for name in mac17-install mac17-usb-backup nmtui cryptsetup lsblk pomona tailscale; do command -v "$name"; done
for name in mac17-browser mac17-onboarding claude gh; do test -x "$target/sw/bin/$name"; done
mac17-install --help
mac17-usb-backup
backup_source=$(findmnt -rn -o SOURCE -T /media/mac17-backup)
iso_source=$(findmnt -rn -o SOURCE -T /iso)
test "$(findmnt -rn -o FSTYPE -T /iso)" = iso9660
test "$(findmnt -rn -o FSTYPE -T /media/mac17-backup)" = vfat
test "$backup_source" != "$iso_source"
backup_disk=$(lsblk -snrpo NAME,TYPE "$backup_source" | awk '$2 == "disk" {print $1}')
iso_disk=$(lsblk -snrpo NAME,TYPE "$iso_source" | awk '$2 == "disk" {print $1}')
test -n "$backup_disk" && test "$backup_disk" = "$iso_disk"
test "$(lsblk -dnro TRAN "$iso_disk")" = usb
printf 'Nonsecret final ISO guest probe\n' > /media/mac17-backup/efi-guest-proof.txt
sync -f /media/mac17-backup/efi-guest-proof.txt
umount /media/mac17-backup
mac17-usb-backup
grep -Fx 'Nonsecret final ISO guest probe' /media/mac17-backup/efi-guest-proof.txt
umount /media/mac17-backup
printf '\n=== Live ISO block layout ===\n'
lsblk -o NAME,TRAN,SIZE,TYPE,LABEL,FSTYPE,MOUNTPOINTS
printf '\n=== Failed units (reported without suppression) ===\n'
systemctl --failed --no-legend --plain
printf '\n=== Required live services ===\n'
systemctl is-active NetworkManager tailscaled sshd
printf '\n=== Offline receipt ===\n'
ip -br link
ip route
printf '\nMAC17_ISO_GUEST_CHECKS_PASS\n'
