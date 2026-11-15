# Disposable installer qualification

This experiment executes the complete installer in a NixOS QEMU guest, under
`runtime-test --allow-kvm` on strix-coordinator. Only guest-created sparse disk
images are exposed. No host block device, credentials, original Mac firmware,
or serial number is passed to the guest.

The guest uses the repository's pinned current nixpkgs
`d5cc6833999746cffdfe0598f7bc801a57b887a9` and stable Linux 7.3.4. OVMF
boots the guest directly with its kernel/initrd, preserving real EFI sysfs
without depending on the test framework's legacy SCSI boot disk. Synthetic
SMBIOS identifies QEMU and MacBookPro14,3. An explicitly synthetic Apple SSD
product and serial identify the disposable 64 GiB disk.

Fixtures: GPT partition 1 (256 MiB FAT ESP), partition 2 Apple APFS type, three
nonsecret dummy T1 files. A different 2 GiB guest block disk holds backups.
The default target is a real minimal NixOS system using the exact copied
production storage-contract; it is not a substitute for the final desktop
closure proof. The expression accepts `targetSystem` and `targetSource` store
path arguments to repeat against the final release payload.

The test uses an actual PTY, no bypasses in the production installer, native
partitioning, FAT/ext4, LUKS2, Nix local-store registration, nixos-install,
GRUB EFI installation, and passwd. All fixture passphrases are synthetic.

Run (after staging source on compute and checking >=25 GiB free):

```sh
fleet-exec strix-coordinator --cwd /tmp/mac17-installer-proof -- df -h /
fleet-exec strix-coordinator --cwd /tmp/mac17-installer-proof -- \
  /home/tom/.local/bin/runtime-test --allow-kvm -- \
  nix build --impure --expr 'import ./test.nix {}' --no-link
```

For final payload: `--expr 'import ./test.nix { targetSystem = "/nix/store/...";
targetSource = "/nix/store/..."; }'`. Those paths must already exist on compute.

Independent defects found and corrected in canonical source by parent:

1. `lsblk -dnro MODEL` hex-escapes spaces, preventing the Apple SSD guard
   from matching real Apple names. Drop raw mode only for MODEL.
2. Current util-linux JSON does not include `children` when NAME is absent
   unless `--tree` is explicit. Add `--tree` to every JSON lsblk invocation
   consumed as a tree, both original layout and new-partition lookup.
3. The root mount assumes `/mnt` exists. A clean NixOS guest does not create
   it; explicitly create the mount point immediately before mounting root.
4. The read-only bundled store is registered without cache signatures, and
   the custom local target closure is unsigned. A fresh destination rejects
   the original local `nix copy` with a missing trusted signature. Add
   `--no-check-sigs` only to the trusted prepared-medium copy command;
   retain normal signature checks globally and keep substitutions disabled.

These tests do not establish that the ISO boots a real Mac, that its keyboard,
Wi-Fi, T1, audio, GPU or suspend function, or that the installed target reboots
from physical Apple firmware. Those remain separate hardware acceptance work.

Optional `usbImage = "/nix/store/.../iso/mac17-installer.iso"` attaches the
single-USB fixture through an emulated xHCI USB-storage disk with a temporary
QEMU snapshot overlay. The immutable source image is never written. The guest
mounts its real ISO9660 partition at `/iso`, runs the exact backup-mount helper,
writes a nonsecret sentinel to the appended MAC17SAVE FAT32 partition, unmounts
and remounts it, and verifies the sentinel plus parent disk identity. Existing
separate backup media remains used for the repeated destructive-install tests.

The initial minimal real-system proof passed all six scenarios in 221.95s.
See `evidence-minimal.json` for exact installer hash, target and result store
paths. The optional USB path was added afterward and is separately qualified.

The optional single-USB helper proof passed in 34.35s. See `evidence-usb.json`.

Repository integration can pass `installerScript` and `storageModule` paths
to reference the canonical modules directly. Final desktop installs allow
1800 seconds per PTY operation and 2400 seconds for the overall install.

## Complete desktop payload

The exact released desktop target (11.6 GiB) passed all six scenarios in
410.39 seconds. See `evidence-final.json` for the source commit, hashes,
compiled target and proof result. The installer explicitly used `nix --offline
copy`, disabled substitutions/builders and asserted no IPv4 default route.
The QEMU default NIC was nevertheless present in that historical test;
`networkingOptions = []` alone did not remove it. Earlier evidence wording
claiming zero guest NICs has been corrected. Future harness runs explicitly
pass `-nic none`. The final release ISO's independent EFI boot probe did use
`-nic none` and checked the complete bundled target closure without host shares.
