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

Name the download `mac17-nixos-YYYY-MM-DD.iso`, generate `SHA256SUMS` from that
filename, and publish both on GitHub Releases using `gh`. Include the Tarek
instructions as an asset so he can keep an offline copy. GitHub's per-release
asset size limit must be checked against the finished ISO; do not publish a
truncated file or mislabel a compressed file as an ISO.

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
