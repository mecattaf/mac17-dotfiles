set -euo pipefail
umask 077
fail() { printf 'mac17-usb-backup: %s\n' "$*" >&2; exit 1; }
[[ $# == 0 ]] || fail 'this command takes no arguments'
[[ $(id -u) == 0 ]] || fail 'run from the prepared live USB with sudo'

# Find the medium actually supplying the live ISO. Do not trust a globally
# ambiguous /dev/disk/by-label link or guess which USB the user inserted.
[[ $(findmnt -rn -o FSTYPE -T /iso) == iso9660 ]] || fail '/iso is not the mounted live ISO filesystem'
source_device=$(findmnt -rn -o SOURCE -T /iso)
source_device=${source_device%%\[*}
source_device=$(readlink -f -- "$source_device")
[[ -b "$source_device" ]] || fail 'the live ISO is not on block media'
ancestors=$(lsblk --tree -s -J -p -o NAME,TYPE "$source_device")
disks=$(jq -c '[.. | objects | select(.type? == "disk") | .name] | unique' <<<"$ancestors")
[[ $(jq 'length' <<<"$disks") == 1 ]] || fail 'cannot determine the single disk supplying the live ISO'
usb_disk=$(jq -r '.[0]' <<<"$disks")
[[ $(lsblk -dnro TRAN "$usb_disk") == usb ]] || fail 'the live ISO is not running from a USB disk'
layout=$(lsblk --tree -J -p -o NAME,TYPE,LABEL,FSTYPE "$usb_disk")
candidates=$(jq -c '[.. | objects | select(.type? == "part" and .label? == "MAC17SAVE" and .fstype? == "vfat") | .name] | unique' <<<"$layout")
[[ $(jq 'length' <<<"$candidates") == 1 ]] || fail 'the live USB has no unique MAC17SAVE backup partition; provide separate writable backup media'
backup_device=$(jq -r '.[0]' <<<"$candidates")
[[ -b "$backup_device" && "$backup_device" != "$source_device" ]] || fail 'invalid backup partition'

destination=/media/mac17-backup
[[ ! -L "$destination" ]] || fail 'the backup mount point is a symlink'
install -d -m 0700 -o root -g root "$destination"
if mountpoint -q "$destination"; then
  mounted_device=$(findmnt -rn -o SOURCE -T "$destination")
  [[ $(readlink -f -- "$mounted_device") == "$backup_device" ]] || fail 'the backup mount point contains another filesystem'
  [[ $(findmnt -rn -o FSTYPE -T "$destination") == vfat ]] || fail 'the mounted backup filesystem is not FAT'
else
  # No formatting, partition editing or whole-device writes occur here.
  mount -t vfat -o rw,nosuid,nodev,noexec,fmask=0177,dmask=0077 "$backup_device" "$destination"
fi
[[ ,$(findmnt -rn -o OPTIONS -T "$destination"), == *,rw,* ]] || fail 'the backup partition is read-only'
[[ -f "$destination/.mac17-backup" ]] || fail 'the backup partition marker is absent'
[[ $(cat "$destination/.mac17-backup") == mac17-usb-backup-v1 ]] || fail 'the backup partition marker is invalid'
printf '%s\n' "$destination"
