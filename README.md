# Tarek's MacBook Pro desktop

A fresh NixOS configuration for the **15-inch 2017 MacBook Pro, MacBookPro14,3
(A1707, Apple T1)**. The prepared USB contains the installed system's complete
closure: Imagine on Domicile, Chrome, Kitty, free AI clients, optional Claude
Code, DSH, GitHub CLI and
Cloudflare Wrangler, alongside native Mac hardware packages.

The current input is NixOS unstable, locked to a reviewed revision, with
`linuxPackages_latest`: **Linux 7.3.4** on 15 November 2026. Imagine is derived
from Manganese and comes from [agency-agency/imagine](https://github.com/agency-agency/imagine).
No device uses another person's accounts, private keys or personalized firmware.

## Start here

- **Tarek and his personal AI:** [Start the step-by-step guides](docs/README.md).
- [Compact download, flashing and first-login instructions](docs/START-HERE.md).
- **Tom:** [Build and release](docs/BUILD-AND-RELEASE.md).
- [Research and source comparisons](docs/research/).
- [Lessons from Tom's system](docs/research/tom-dotfiles.md).
- [Free AI accounts and working entry points](docs/free-ai.md).
- [DSH and maintained dshd updates](docs/dsh-runtime.md).
- [Retina display preferences](docs/retina-display.md).

Release assets are published with a source revision and SHA-256 checksum.
Build success and real Mac hardware acceptance are recorded separately.

## System shape

`hosts/mac17` composes the independent device. `modules/storage-contract.nix`
defines encrypted ext4 root, a separate Linux `/boot` and the existing Apple
EFI partition mounted at `/boot/efi`. The installer preserves and checks the
T1 firmware before and after partitioning and bootloader installation.

`modules/macbookpro14-3.nix` supplies Pomona's T1 core, early SPI input,
BCM43602 board configuration, current CS8409 audio support, fans and sensors.
The optional full-pixel Touch Bar driver is a separate build output; competing
T1 stacks are never enabled together.

Accounts and mutable application settings stay in their native writable
stores. Rebuilding the system does not overwrite OAuth refresh state or
Chrome profiles. Root SSH is key-only on the tailnet interface for explicitly
authorized management; the included public key is revocable in `keys/`.

The repository starts under `mecattaf`, shared with `tarekcmahmoud`. Tom will
transfer ownership to Tarek. GitHub redirects preserve old repository links;
the configured remote should be updated after the transfer.
