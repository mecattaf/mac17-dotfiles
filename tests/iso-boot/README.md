# Final image EFI USB boot proof

The exact release image passed the live checks in `guest-checks.sh`; see
[evidence-iso.json](evidence-iso.json) and [serial.txt](serial.txt).
The prepared target/source match release commit `af5434b`, and all 1,731
registered target-closure paths exist on the booted image. The independently
recomputed whole-image SHA256 matches the release checksum.

The image booted through OVMF's USB EFI entry and the maintained ISO default
GRUB entry into its normal live login. Kernel arguments were unchanged.
A guest-only `serial-getty@ttyS0.service` was started from the VGA console
using `qmp-type.py` for inspection. This is console access within the
throwaway guest; no host session or service was changed.

The backup helper located the appended MAC17SAVE FAT32 partition from the
mounted live ISO, wrote and fsynced a sentinel, then unmounted/remounted and
read it. NetworkManager, tailscaled and sshd were active. The exact guest
command includes `-nic none`; only loopback and unauthenticated tailscale0
appeared, with no default route. No authentication or account enrollment ran.

The only failed live unit was mbpfan: this AMD-host QEMU exposes no Intel
coretemp or Apple SMC. Its journal failure is retained in the serial receipt.
The maintained NixOS module already declares coretemp and applesmc; real
fan/sensor operation remains physical hardware acceptance.

## Harness

Run `boot-iso.py` only on compute through `runtime-test --allow-kvm`. Its
storage is the immutable final image attached as xHCI USB-storage using
`snapshot=on`, plus private OVMF variables. No host block device, home,
credentials, shared host Nix store, or network interface enters the guest.
The realized QEMU lacks libpng, so exact PPM captures are encoded losslessly
as PNG with the Python standard library; no new QEMU build was needed.

```sh
fleet-exec strix-coordinator --cwd /absolute/checkout -- \
  /home/tom/.local/bin/runtime-test --allow-kvm -- \
  python3 tests/iso-boot/boot-iso.py \
  --iso /nix/store/RELEASE-OUTPUT/iso/mac17-installer.iso \
  --work /tmp/mac17-iso-proof/probe
```

The harness accepts JSON requests on stdin: `key`, `capture`, `serial`,
`guest_script`, `status`, `quit`. Its QMP and serial sockets control only
that guest. `qmp-type.py` can type the short console command
`sudo systemctl start serial-getty@ttyS0.service` after the live login.
Then send `guest_script` with the absolute compute path to `guest-checks.sh`.
`quit` stopped the tested guest cleanly with exit 0.

This proves emulated EFI USB boot, the actual live environment and prepared
payload presence. It does not establish physical Mac boot, hardware behavior,
installed desktop reboot, or browser/keyring sign-in. The separate
[installer proof](../installer-vm/evidence-final.json) executes complete
installation of the exact desktop closure onto disposable encrypted storage.

`serial.txt` is a readable normalization of the terminal receipt: escape
sequences and carriage-return formatting removed. `serial.raw.gz` preserves
the byte-exact original, including the reported fan-service failure.
