#!/usr/bin/env bash
# This program is destructive only with --install AND an on-device phrase.
# Never source this file. Syntax checks do not execute its commands.
set +x
set -euo pipefail
umask 077

fail() { printf 'mac17-install: %s\n' "$*" >&2; exit 1; }
usage() {
  cat <<'HELP'
Usage: mac17-install --disk /dev/disk/by-id/<internal-Apple-SSD>
       mac17-install --disk /dev/disk/by-id/<internal-Apple-SSD> \
         --install [--backup-dir /path/on/another/writable/disk]

The first command only checks and prints a plan. The second backs up the
Apple EFI partition and GPT to separate media, requires a typed confirmation,
then replaces macOS with the exact NixOS system already on the USB.
The prepared USB includes its own writable backup partition. An explicit
--backup-dir can select other writable block media instead.
The Apple ESP, including its T1 firmware, is retained. Its GPT name becomes
MAC17_EFI; its location, type, UUID and filesystem contents are preserved.
No Wi-Fi password or account credential is needed to install the base system.
HELP
}

disk_arg=""; backup_dir=""; do_install=false
while (($#)); do
  case "$1" in
    --disk) (($# >= 2)) || fail '--disk needs a path'; disk_arg=$2; shift 2 ;;
    --backup-dir) (($# >= 2)) || fail '--backup-dir needs a path'; backup_dir=$2; shift 2 ;;
    --install) do_install=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
done
[[ -n "$disk_arg" ]] || { usage; exit 1; }
[[ $(id -u) == 0 ]] || fail 'run this from the live USB with sudo'
[[ -t 0 ]] || fail 'a local interactive terminal is required'
[[ -d /sys/firmware/efi ]] || fail 'boot the USB through the Mac EFI boot picker'
[[ $(cat /sys/class/dmi/id/product_name) == 'MacBookPro14,3' ]] || fail 'this installer is only for MacBookPro14,3'
[[ "$disk_arg" == /dev/disk/by-id/* ]] || fail 'select an explicit persistent /dev/disk/by-id/ path'
[[ -L "$disk_arg" && -b "$disk_arg" ]] || fail 'the selected disk is not an existing block-device link'
disk=$(readlink -f -- "$disk_arg")
[[ $(lsblk -dnro TYPE "$disk") == disk ]] || fail 'select the whole internal disk, not a partition'
[[ $(lsblk -dnro RM "$disk") == 0 ]] || fail 'the selected disk reports removable media'
[[ $(lsblk -dnro TRAN "$disk") != usb ]] || fail 'the selected disk is on USB'
model=$(lsblk -dn -o MODEL "$disk" | sed 's/[[:space:]]*$//')
[[ "$model" == APPLE\ SSD* ]] || fail 'the selected disk does not identify as an internal Apple SSD'
(( $(blockdev --getsize64 "$disk") >= 64000000000 )) || fail 'the selected disk is smaller than 64 GB'
[[ $(blkid -p -s PTTYPE -o value "$disk") == gpt ]] || fail 'the selected disk must have an existing Apple GPT'
[[ ! -e /dev/mapper/mac17-root ]] || fail 'mac17-root already exists; inspect the previous attempt before proceeding'
! mountpoint -q /mnt || fail '/mnt is already mounted'

layout=$(lsblk --tree -J -b -o PATH,TYPE,SIZE,FSTYPE,PARTTYPE,PARTN,PARTUUID,MOUNTPOINTS "$disk")
jq -e '[.. | objects | .mountpoints? // [] | .[] | select(. != null and . != "")] | length == 0' <<<"$layout" >/dev/null || fail 'a filesystem on the target is mounted'
jq -e '[.blockdevices[0].children[]? | select(.type != "part")] | length == 0' <<<"$layout" >/dev/null || fail 'the target has active device-mapper or other child devices'
esp_guid='c12a7328-f81f-11d2-ba4b-00a0c93ec93b'
esp_count=$(jq --arg t "$esp_guid" '[.blockdevices[0].children[]? | select((.parttype // "" | ascii_downcase) == $t)] | length' <<<"$layout")
[[ "$esp_count" == 1 ]] || fail 'exactly one existing EFI System Partition is required'
esp=$(jq -r --arg t "$esp_guid" '.blockdevices[0].children[] | select((.parttype // "" | ascii_downcase) == $t) | .path' <<<"$layout")
esp_number=$(jq -r --arg e "$esp" '.blockdevices[0].children[] | select(.path == $e) | .partn' <<<"$layout")
[[ "$esp_number" == 1 ]] || fail 'the preserved Apple EFI partition must be partition 1'
[[ $(blkid -s TYPE -o value "$esp") == vfat ]] || fail 'the existing EFI partition is not FAT'
# Initial migration supports known Apple layouts only. Do not reinterpret an
# existing Linux install or an unfamiliar layout as disposable macOS data.
jq -e --arg t "$esp_guid" '
  [.blockdevices[0].children[]? | (.parttype // "" | ascii_downcase)]
  | all(. == $t or . == "7c3457ef-0000-11aa-aa11-00306543ecac"
    or . == "48465300-0000-11aa-aa11-00306543ecac"
    or . == "426f6f74-0000-11aa-aa11-00306543ecac")
' <<<"$layout" >/dev/null || fail 'an unexpected partition type needs a reviewed installation plan'
[[ -n ${MAC17_TARGET_SYSTEM:-} && -x "$MAC17_TARGET_SYSTEM/bin/switch-to-configuration" ]] || fail 'the prepared target system is absent'
[[ -d ${MAC17_TARGET_SOURCE:-} && -f "$MAC17_TARGET_SOURCE/flake.lock" ]] || fail 'the pinned target source and flake.lock are absent'

esp_mount=$(mktemp -d /tmp/mac17-esp.XXXXXX)
mounted_root=false; opened_root=false
cleanup() {
  local status=$?
  trap - EXIT
  # Only release mounts/devices created by this invocation. No runtime tree or
  # user-manager cleanup, no reboot, no filesystem rollback is attempted.
  if mountpoint -q "$esp_mount"; then umount "$esp_mount" || true; fi
  rmdir "$esp_mount" 2>/dev/null || true
  if "$mounted_root"; then umount -R /mnt || true; fi
  if "$opened_root"; then cryptsetup close mac17-root || true; fi
  exit "$status"
}
trap cleanup EXIT
mount -o ro,nosuid,nodev,noexec "$esp" "$esp_mount"
for name in combined.memboot FDRData version.plist; do
  [[ -s "$esp_mount/EFI/APPLE/EMBEDDEDOS/$name" ]] || fail "Apple T1 firmware is missing $name; repair it in macOS before installation"
done
firmware_digest() {
  (
    cd "$1"
    find EFI/APPLE/EMBEDDEDOS -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
  )
}
firmware_before=$(firmware_digest "$esp_mount")
esp_uuid_before=$(blkid -s PARTUUID -o value "$esp")
esp_geometry_before=$(sfdisk --json "$disk" | jq -c --arg e "$esp" '.partitiontable.partitions[] | select(.node == $e) | {start,size,type,uuid}')

printf '\nTarget: %s\nModel: %s\n' "$disk_arg" "$model"
lsblk -o NAME,SIZE,TYPE,FSTYPE,PARTLABEL,MOUNTPOINTS "$disk"
printf '\nKeep: %s, Apple EFI + T1 firmware\nCreate: 2 GiB ext4 /boot; LUKS2 + ext4 / on remaining space\nSystem: %s\nSource: %s\n\n' "$esp" "$MAC17_TARGET_SYSTEM" "${MAC17_SOURCE_REVISION:-unknown}"
if ! "$do_install"; then
  printf 'Plan only. Nothing has been changed. Use --install after review. The prepared USB stores the firmware backup.\n'
  exit 0
fi

if [[ -z "$backup_dir" ]]; then
  backup_dir=$(mac17-usb-backup) || fail 'cannot mount the prepared USB backup partition; provide --backup-dir on separate writable block media'
fi
[[ -d "$backup_dir" && -w "$backup_dir" ]] || fail '--backup-dir must be an existing writable directory on another disk'
backup_dir=$(realpath -- "$backup_dir")
backup_source=$(findmnt -rn -o SOURCE -T "$backup_dir")
backup_source=${backup_source%%\[*}
[[ -b "$backup_source" ]] || fail 'the backup directory must be on separately mounted writable block media'
backup_source=$(readlink -f -- "$backup_source")
if lsblk -snrpo NAME "$backup_source" | grep -Fxq "$disk"; then fail 'the backup directory is on the disk that would be erased'; fi
# Reserve enough room even if the ESP image compresses poorly. Never remove
# an older backup automatically. Every write and verification precedes erasure.
esp_size=$(blockdev --getsize64 "$esp")
efi_size=$(du -sb "$esp_mount/EFI" | cut -f1)
required_space=$((esp_size + esp_size / 100 + efi_size + 16 * 1024 * 1024))
available_space=$(df -B1 --output=avail "$backup_dir" | tail -n1)
(( available_space >= required_space )) || fail 'insufficient backup space; copy earlier USB backups somewhere safe or supply larger --backup-dir media'
backup=$(mktemp -d "$backup_dir/mac17-efi-$(date -u +%Y%m%dT%H%M%SZ).XXXXXX")
sgdisk --backup="$backup/original-gpt.bin" "$disk"
dd if="$esp" bs=4M status=progress | gzip -1 > "$backup/apple-esp.img.gz"
gzip -t "$backup/apple-esp.img.gz"
[[ $(gzip -dc "$backup/apple-esp.img.gz" | wc -c) == "$esp_size" ]] || fail 'the raw ESP backup has an unexpected size'
tar -C "$esp_mount" -czf "$backup/apple-efi-files.tar.gz" EFI
printf '%s\n' "$firmware_before" > "$backup/t1-files.sha256"
printf '%s\n' "$esp_geometry_before" > "$backup/esp-geometry.json"
cp /etc/mac17/install/image.json "$backup/image.json"
(
  cd "$backup"
  sha256sum apple-esp.img.gz original-gpt.bin apple-efi-files.tar.gz > SHA256SUMS
  sha256sum --check SHA256SUMS
)
sync -f "$backup/apple-esp.img.gz"
printf '\nVerified EFI backup: %s\n' "$backup"
printf 'macOS and all other partitions on %s will now be erased.\n' "$disk_arg"
read -r -p 'Type INSTALL MAC17 to continue: ' answer
[[ "$answer" == 'INSTALL MAC17' ]] || fail 'installation cancelled'
read -r -s -p 'Choose the disk-unlock passphrase: ' disk_passphrase; printf '\n'
read -r -s -p 'Repeat the disk-unlock passphrase: ' repeat_passphrase; printf '\n'
[[ -n "$disk_passphrase" && "$disk_passphrase" == "$repeat_passphrase" ]] || fail 'disk passphrases do not match or are empty'
unset repeat_passphrase

umount "$esp_mount"
# Partition 1 stays in place. Deleting other GPT entries does not format or
# move the ESP. We never run wipefs, mklabel, --zap-all or a whole-disk dd.
while read -r n; do sgdisk --delete="$n" "$disk"; done < <(jq -r --arg e "$esp" '.blockdevices[0].children[] | select(.path != $e) | .partn' <<<"$layout")
sgdisk --change-name=1:MAC17_EFI \
  --new=2:0:+2G --typecode=2:8300 --change-name=2:MAC17_BOOT \
  --new=3:0:0 --typecode=3:8309 --change-name=3:MAC17_CRYPT "$disk"
partprobe "$disk"
udevadm settle
boot_part=$(lsblk --tree -J -o PATH,PARTN "$disk" | jq -r '.blockdevices[0].children[] | select((.partn | tonumber) == 2) | .path')
root_part=$(lsblk --tree -J -o PATH,PARTN "$disk" | jq -r '.blockdevices[0].children[] | select((.partn | tonumber) == 3) | .path')
[[ -b "$boot_part" && -b "$root_part" ]] || fail 'new target partitions did not appear'
[[ $(blkid -s PARTUUID -o value "$esp") == "$esp_uuid_before" ]] || fail 'the preserved ESP partition UUID changed'
esp_geometry_after=$(sfdisk --json "$disk" | jq -c --arg e "$esp" '.partitiontable.partitions[] | select(.node == $e) | {start,size,type,uuid}')
[[ "$esp_geometry_after" == "$esp_geometry_before" ]] || fail 'the preserved ESP geometry changed'

printf '%s' "$disk_passphrase" | cryptsetup luksFormat --batch-mode --type luks2 --label MAC17_CRYPT --key-file=- "$root_part"
printf '%s' "$disk_passphrase" | cryptsetup open --key-file=- "$root_part" mac17-root
unset disk_passphrase
opened_root=true
mkfs.ext4 -L MAC17_BOOT "$boot_part"
mkfs.ext4 -L MAC17_ROOT /dev/mapper/mac17-root
mkdir -p /mnt
mount /dev/mapper/mac17-root /mnt
mounted_root=true
mkdir -p /mnt/boot
mount "$boot_part" /mnt/boot
mkdir -p /mnt/boot/efi
mount -o umask=0077 "$esp" /mnt/boot/efi
[[ $(firmware_digest /mnt/boot/efi) == "$firmware_before" ]] || fail 'the retained T1 firmware content changed'

# Install the exact closure. No evaluation/build of a modified configuration
# occurs on the laptop. The first copy must succeed without substitutions.
nix --extra-experimental-features 'nix-command flakes' --offline copy --no-check-sigs \
  --to 'local?root=/mnt' "$MAC17_TARGET_SYSTEM"
nixos-install --root /mnt --system "$MAC17_TARGET_SYSTEM" \
  --no-channel-copy --no-root-passwd --option substitute false
mkdir -p /mnt/etc/nixos /mnt/var/lib/mac17-install
cp -a "$MAC17_TARGET_SOURCE/." /mnt/etc/nixos/
cp /etc/mac17/install/image.json /mnt/var/lib/mac17-install/image.json
printf '%s\n' "$firmware_before" > /mnt/var/lib/mac17-install/t1-files.sha256
[[ $(firmware_digest /mnt/boot/efi) == "$firmware_before" ]] || fail 'T1 firmware changed during bootloader installation'
printf '\nSet Tarek\047s Linux login password. This is separate from the disk-unlock passphrase.\n'
nixos-enter --root /mnt -c 'passwd tarek'
sync
printf '\nInstallation finished. Remove the USB and restart when ready.\nThe first account action is Google Chrome sign-in after connecting to Wi-Fi.\n'
