# Prepared installer: 15 November 2026

**[Download the installer ZIP](https://github.com/mecattaf/mac17-dotfiles/actions/runs/43764951494/artifacts/14181806726)** while signed in as **tarekcmahmoud**.
Extract it. The file to flash is **mac17-installer.iso**. The image is 5.2 GB;
use an 8 GB or larger USB (16 GB recommended).

Start at [the guide index](README.md). Give your personal AI that index and
only the current phase. Each phase has its own actions, definition of done
and stop conditions. Keep the guide and chat on another device before wiping.

The USB contains the full desktop and applications. Wi-Fi is entered in the
installed desktop; it is not needed to fetch programs during installation.
Accounts belong to you. Claude Code is optional. Start free AI using
[phase 4](04-free-ai.md).

## Verified before publishing

- Linux 7.3.4, latest stable selected by this reviewed Nixpkgs input.
- All 46 integrated checks passed.
- Complete 11.6 GiB offline desktop installation passed six test scenarios.
- The actual image booted through EFI USB in a disposable VM; all 1,731
  prepared closure paths and the writable USB backup partition were checked.
- GitHub reconstructed and checked the complete ISO before uploading this ZIP.

The VM lacks Intel temperature sensors and Apple SMC; its recorded fan-service
failure is expected for that emulation. Physical Mac boot, Wi-Fi, audio,
Touch Bar, camera, cooling and desktop sign-in remain to be checked in
[phase 5](05-verify-and-contribute.md). Sleep stays disabled until qualified.

Built source: `af5434b66b388e9a8b0bd9ac3d4b3f724df566d6`.
ISO SHA-256: `9f11271addf7a553c67d30a29649e30bdd70f501a54d82ac5a5900d3932a6296`.
The downloaded `BUILD-MANIFEST.json` records all input pins and the guide revision.

The convenient ZIP expires **22 November 2026**. [Release assets](https://github.com/mecattaf/mac17-dotfiles/releases/tag/v2026.11.15)
keep the image parts and guides. Tom can rerun **Prepare ISO download** to
refresh the link; do not flash a `.part-*` file. See [reassembly instructions](BUILD-AND-RELEASE.md).
