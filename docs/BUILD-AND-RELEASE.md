# Build and release the prepared USB

Build on an x86_64 NixOS machine. On Tom's fleet, stage this checkout on
strix-coordinator without credentials and use `fleet-exec`. Check `df -h /`
on the build host before every Nix build; stop below 25 GiB free.

```sh
nix build .#desktop-config -L
nix build .#system -L
nix build .#iso -L --out-link result-iso
```

The ISO's `isoImage.storeContents` includes the exact system closure and this
locked source tree. `mac17-install` copies that closure without substitution
and passes it to the maintained `nixos-install --system`; it does not evaluate
a second configuration or build packages on Tarek's laptop.

Record the source commit, lock pins, kernel version, system store path, ISO
size and SHA-256 in the release notes. Check the finished USB image's partition
table/EFI boot data and test its boot and installer path in a disposable VM.
The destructive installer must never run against a host disk during tests.
Use the target `runtime-test` wrapper around runtime-sensitive tests.

The build output is `result-iso/iso/mac17-installer.iso` and its `SHA256SUMS`.
`packages.raw-iso` exposes the maintained base ISO; the default `iso` output
replays its existing boot equipment and appends an initially empty 512 MiB
FAT32 **MAC17SAVE** partition. The installer identifies that partition on the
actual boot USB and saves firmware there before any erase. No personalized
firmware or account state belongs in a downloadable image.

GitHub Releases limits each asset to 2 GiB. For a larger image, preserve it as
ordered `mac17-installer.iso.part-aa`, `part-ab`, ... assets below that limit,
plus `PARTS-SHA256SUMS`, the complete image's `SHA256SUMS`, `START-HERE.md` and
`BUILD-MANIFEST.json`. Do not flash a part. The manual **Prepare ISO download**
workflow verifies the parts, reconstructs and checks the complete ISO, then
publishes one **mac17-installer** artifact containing the image and guide.
The workflow packages an already compiled image; it does not rebuild NixOS.
Put its actual artifact link in the release notes. Tarek downloads and extracts
that ZIP and flashes the `.iso` inside it. Private repository access requires
accepting his invitation and signing in to GitHub before downloading.

The convenient artifact expires after seven days. The release parts remain:
rerun the workflow with the release tag to create a fresh artifact, or restore
manually with GitHub CLI while signed in to an authorized account:

```sh
mkdir mac17-download
cd mac17-download
gh release download v2026.11.15 --repo mecattaf/mac17-dotfiles
shasum -a 256 -c PARTS-SHA256SUMS
cat mac17-installer.iso.part-* > mac17-installer.iso
shasum -a 256 -c SHA256SUMS
```

The manifest records source and lock pins, compiled system, kernel, complete
ISO size/hash and the validation performed. Source publication, VM success
and actual physical Mac acceptance are distinct claims.

## Update shared software

Keep the base Nixpkgs/kernel, the Domicile SDK+engine, Imagine and llm-agents
as separately reviewed inputs. "Latest" means deliberately updating their
locked versions, building the result and applying it; it does not mean
different machines fetching unreviewed main during login.

The llm-agents input currently exports `packages.<system>` and
`overlays.shared-nixpkgs`; it no longer exports the `overlays.default` mentioned
in older dotfiles comments. This configuration consumes the prebuilt package
set directly and trusts the catalog's signed cache. Keep its own Nixpkgs pin
to retain substitutes instead of rebuilding its whole catalog against ours.

Before a managed switch, inspect its activation plan and retain the previous
generation. Do not restart a running user manager or desktop to make an update
look successful. Root SSH uses the owner's tailnet and the public management
key in `keys/managers.pub`; no manager private key is delivered to the Mac.
