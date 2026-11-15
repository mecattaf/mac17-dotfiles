# Prepared USB installation and account persistence for Tarek

The recommended installation is an official NixOS installer ISO carrying the **complete, already built Mac17 system closure and its pinned source**. It installs that exact closure locally, preserves Apple's existing EFI partition, and creates encrypted persistent storage. Wi-Fi and account sign-ins happen after installation. The installed desktop and command-line tools are already present; account authorization and Chrome Sync still require the network.

This uses maintained NixOS building and installation mechanisms. It does not need a new distribution framework, a bespoke image updater, or an Internet bootstrap on the laptop.

## Mechanisms reviewed

| Mechanism | What it provides | Fit for this device |
|---|---|---|
| Official NixOS ISO module | EFI/USB boot, live environment, full Nix store closures via `isoImage.storeContents` | Recommended foundation; import the Mac hardware support into both live and installed configurations |
| `nixos-rebuild build-image` | Maintained image variants, upstreamed from nixos-generators since NixOS25.05 | Current image-building entry point; a separate installer configuration can also expose `config.system.build.isoImage` directly |
| nixos-generators | Older wrapper for image formats | Upstream declares it deprecated; adding it as a new dependency buys nothing here |
| `nixos-install --system STORE_PATH` | Installs an existing system closure instead of evaluating/building a new one | Recommended installation step; same target derivation built before composing the USB |
| disko | Declarative disk/format/mount scripts and image support | Useful for standard fresh disks, but ordinary destroy/format modes are the wrong default for the personalized Apple ESP. Current disk type has `destroy=false`; that alone does not imply each child filesystem will be preserved. A retained Apple partition needs an explicit reviewed preservation strategy |
| nixos-anywhere | Remote SSH orchestration, kexec, disko, system installation and file delivery | Good alternative when Tom is online and controlling installation; target must already be Linux or the NixOS installer. It does not replace macOS directly, and its documented requirements do not support Wi-Fi through the kexec transition |
| nix-community/nixos-images | Weekly bootable remote-friendly installers, random password, QR, IWD, SSH and Tor | Good generic recovery/online installation media; does not preload Tarek's packages or all his Mac firmware fixes. No reason to add Tor or another Wi-Fi manager to the prepared image |
| Clan | Managed inventory, generated secrets, hardware discovery, remote installation and deployment | Credible mature fleet platform. Its documented physical-machine path still needs network/SSH and builds/deploys the machine configuration. Adopting its inventory, vars and connectivity model is unnecessary for this one independently owned dotfiles repository and existing Tailscale workflow |
| nixos-facter / nixos-hardware | Captures factual hardware / supplies maintained hardware modules | Useful discovery inputs. They cannot infer account authorization, personalized T1 firmware, UX policy, or certify suspend and audio. Keep generated hardware facts distinct from authored desktop defaults |
| Raw disk image / systemd-repart | Prebuilt partition/filesystem images and appliance workflows | Attractive for standard appliances. Whole-disk image writing is a poor match for retaining the Mac's machine-specific ESP. Use the prepared installer rather than copying a raw image over the internal SSD |

Sources: [official ISO source](https://github.com/NixOS/nixpkgs/blob/f1e5c356f35d07e7b71a6b5e6c9338e0b029e0c0/nixos/modules/installer/cd-dvd/iso-image.nix), [official installer source](https://github.com/NixOS/nixpkgs/blob/f1e5c356f35d07e7b71a6b5e6c9338e0b029e0c0/pkgs/by-name/ni/nixos-install/nixos-install.sh), [image-building manual](https://nixos.org/manual/nixos/stable/#sec-image-building), [nixos-generators deprecation](https://github.com/nix-community/nixos-generators/blob/8946737ff703382fda7623b9fab071d037e897d5/README.md), [disko disk implementation](https://github.com/nix-community/disko/blob/1dd30c29c88d99ce295f15e27f93c49bc5fbae07/lib/types/disk.nix), [disko GPT implementation](https://github.com/nix-community/disko/blob/1dd30c29c88d99ce295f15e27f93c49bc5fbae07/lib/types/gpt.nix), [nixos-anywhere requirements](https://github.com/nix-community/nixos-anywhere/blob/58132e1d1f813b845382a2aeca4203b18d2ac807/docs/requirements.md), [community installer](https://github.com/nix-community/nixos-images/blob/50939ddf1a0339f289a9dbd810bdfd4e4fba6df4/README.md), [current Clan physical-machine workflow](https://clan.lol/docs/unstable/getting-started/quick-start).

## How the prepared image avoids a second download

Build `nixosConfigurations.mac17.config.system.build.toplevel` on Tom's compute host. Include that output in the separate installer's `isoImage.storeContents`, together with the exact dotfiles source containing `flake.lock`. The ISO builder includes the referenced store closure in its compressed Nix store. When the Mac boots USB, the target packages are already in its local store.

The installer copies the target closure into the destination store with `nix --offline copy --to 'local?root=/mnt' TARGET`, then calls `nixos-install --root /mnt --system TARGET --no-channel-copy --no-root-passwd --option substitute false`. Supplying `--system` bypasses the source evaluation/build branch in the maintained installer. `--no-channel-copy` also avoids unnecessarily installing an entire Nixpkgs channel.

`isoImage.includeSystemBuildDependencies=true` is **not** needed for this path. It carries build inputs and substantially increases image size. The target runtime closure is what makes initial installation work offline. If an offline future rebuild is also desired, separately archive the locked flake input sources and build inputs; carrying installed binaries alone does not make arbitrary future edits buildable offline.

All Nix-managed applications must belong to the target closure, including Home Manager's activation and user packages when Home Manager is integrated into the NixOS system. Do not leave Chrome, Kitty, Domicile, Imagine, Claude Code, DSH or required plugins to first-run `nix profile install`, curl installers, npm installs or dynamic builds. Chrome Sync can download extensions and user data after sign-in; that is separate from installing the base browser.

The image output needs a signed-off source revision, matching Domicile source/SDK/engine, SHA-256 checksum and a durable download URL. A successful Nix build is package/build evidence. It does not certify this Mac's physical keyboard, sound, Touch Bar, thermal behavior or suspend.

## Storage and firmware contract

Keep the existing Apple EFI System Partition in its original location with its existing partition type, UUID and FAT filesystem. Its `EFI/APPLE/EMBEDDEDOS` data is personalized to this machine; do not commit it, put it in the Nix store, or bundle it into a generally downloadable installer. Before any destructive operation, export the existing GPT and raw ESP image plus a file-level archive onto a separate writable disk and verify checksums.

The prepared system uses:

| Mount or identity | Prepared layout |
|---|---|
| Existing Apple ESP | Retained; only its GPT name changes to `MAC17_EFI` for predictable mounting |
| `/boot/efi` | `/dev/disk/by-partlabel/MAC17_EFI`, FAT, `umask=0077` |
| `/boot` | New 2GiB ext4 partition, filesystem label `MAC17_BOOT` |
| Encrypted root container | New LUKS2 partition, LUKS label `MAC17_CRYPT` |
| `/` | ext4 on `/dev/mapper/mac17-root`, inside LUKS2 |
| User and application state | Ordinary persistent encrypted root/home; no impermanence layer required |

Use GRUB with EFI support, `devices=["nodev"]`, removable fallback path, and `canTouchEfiVariables=false`. Kernels and initrds go on the separate ext4 `/boot`; only small EFI bootloader files go on Apple's small ESP. This avoids treating the usual 200–300MB Apple ESP as a kernel store. [Maintained GRUB options and behavior](https://github.com/NixOS/nixpkgs/blob/f1e5c356f35d07e7b71a6b5e6c9338e0b029e0c0/nixos/modules/system/boot/loader/grub/grub.nix).

The supplied installer is deliberately narrow: MacBookPro14,3, an explicit `/dev/disk/by-id/` internal Apple SSD, EFI boot, unmounted known Apple partition types, exactly one first ESP, and present nonempty T1 files. It defaults to printing the plan. Actual installation requires separate backup media, `--install`, a local terminal and the phrase `INSTALL MAC17`. It deletes non-ESP GPT entries, creates `/boot` and encrypted root, and verifies the retained ESP geometry/UUID and T1 file hashes before and after bootloader installation. It never uses `wipefs`, whole-disk `dd`, `mklabel` or `--zap-all` on the target.

An unfamiliar layout stops for a revised plan; it is not silently interpreted as disposable data. An existing Linux installation is outside this initial-migration script's scope. This gives a usable initial installer without pretending a general partition migration engine has been built.

## When Tarek enters Wi-Fi

Preferred path: installation itself is offline. After disk unlock and normal local login, onboarding asks him to choose his network and type the Wi-Fi password into NetworkManager's native secret prompt. Then Chrome sign-in is the first account action. The dotfiles do not need to be fetched over that connection: they are already installed from USB.

Use NetworkManager's existing UI/API, with `nmtui` and `nmcli --ask device wifi connect SSID` as recovery paths. Do not put a PSK in a command argument, Git, the ISO or a Nix string. NetworkManager's system connection keyfiles persist under `/etc/NetworkManager/system-connections` with root-only permissions. They survive rebuilds and ordinary reboots. A session-only secret agent profile instead needs its keyring available, so a managed laptop should deliberately create a persistent connection.

If Tom needs to assist while the live USB is running, Tarek can enter Wi-Fi there first. The live environment is ephemeral; that entry does not automatically appear on the installed system. A deliberate transfer may copy only the selected connection's keyfile to the installed system with root ownership and0600 permissions. Do not copy every connection from Tom's computer or bake this into the Nix store. USB-C Ethernet or an Android phone's USB tethering also permits assistance without depending on the internal Wi-Fi fix.

[NetworkManager examples](https://www.networkmanager.dev/docs/api/latest/nmcli-examples.html), [nmcli persistence semantics](https://networkmanager.dev/docs/api/latest/nmcli), [NixOS ensureProfiles and environment-file source](https://github.com/NixOS/nixpkgs/blob/f1e5c356f35d07e7b71a6b5e6c9338e0b029e0c0/nixos/modules/services/networking/networkmanager.nix).

## Chrome first and a working keyring

A plain Wayland window manager does not automatically provide the Secret Service that Chrome and other clients expect. Enable `services.gnome.gnome-keyring.enable=true`, explicitly wire `security.pam.services.greetd.enableGnomeKeyring=true` if greetd is the login service, and retain password-based login so PAM can unlock the login keyring. The NixOS keyring module only automatically wires the `login` PAM service; greetd requires its own setting.

Force Chrome's `--password-store=gnome-libsecret`, and verify the session bus can activate Secret Service before Chrome's first launch. Chromium's documented behavior is to fall back to its basic store if the requested backend is unavailable, so the flag alone is insufficient proof. Chrome's own profile sign-in and signing into a Google web page are different actions. The onboarding should point at Chrome's native sign-in flow, leave the browser in control of authentication, and let Tarek confirm completion; do not inspect cookies, scrape the account page or fake a successful login from an installed profile directory.

Chrome profile and `~/.local/share/keyrings` must be backed up together. A restored encrypted keyring can require the password with which it was created; changing the Unix password does not prove an old wallet was re-encrypted. Normal NixOS rebuilds do not erase either directory.

[Chromium Linux password storage](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux/password_storage.md), [NixOS keyring module](https://github.com/NixOS/nixpkgs/blob/f1e5c356f35d07e7b71a6b5e6c9338e0b029e0c0/nixos/modules/services/desktops/gnome/gnome-keyring.nix), [NixOS Secret Service PAM guidance](https://wiki.nixos.org/wiki/Secret_Service).

## Tailscale ownership and Tom's access

Tarek signs into the preinstalled Tailscale client using **his** identity. His tailnet remains his. No reusable auth key, preauthenticated state or Tom identity belongs in the ISO. His first `tailscale up` can make `tarek` the local operator; normal OpenSSH over Tailscale is enough for managed NixOS updates.

For the requested administration relationship, he opens the [Users page](https://login.tailscale.com/admin/users), chooses **Invite external users**, chooses **Admin**, generates a one-time invitation link and sends it to Tom. The invitation gives console administration over Tarek's tailnet. Admin is broader than a device share: it includes policy and device administration. Tarek remains Owner. [Official invitation steps](https://tailscale.com/docs/features/sharing/how-to/invite-any-user), [role meanings](https://tailscale.com/docs/reference/user-roles).

That invitation does **not** move Tom's already-running NAS client into Tarek's tailnet or make a single Tailscale client concurrently attach to both. For access from Tom's existing fleet, use one of these explicit paths:

1. Share `mac17` to Tom's own existing Tailscale identity. Allow ordinary TCP22 in the share policy, keep OpenSSH enabled only on `tailscale0`, authorize Tom's management public key, and verify the newly generated SSH host fingerprint before first use. Tom can manage it while his fleet remains on its own tailnet. Admin-console invitation and node sharing serve different purposes and can both be used.
2. Enroll a dedicated management client/instance in Tarek's tailnet. Then use the policy defined for that tailnet. Do not change the NAS's global Tailscale login to achieve this.

Current documentation also permits **Tailscale SSH to a shared tagged device** when the destination policy allows it. Older blanket statements that Tailscale SSH can never work over sharing are no longer correct. Tagging changes a device's identity and ownership semantics, so it should be a deliberate design choice rather than a workaround applied silently to his personal laptop. Ordinary OpenSSH over a shared node keeps the initial path straightforward. Do not enable `tailscale --ssh` and assume it is interchangeable with OpenSSH: Tailscale then claims port22 on its address and uses its own authentication/policy.

[Inviting versus sharing](https://tailscale.com/docs/reference/inviting-vs-sharing), [node sharing](https://tailscale.com/docs/features/sharing), [current Tailscale SSH supported connection types](https://tailscale.com/docs/features/tailscale-ssh).

## CLI sign-ins and durable state

| Account or state | Initial authorization | Durable location / restore rule |
|---|---|---|
| GitHub | `gh auth login --web --git-protocol https`, then `gh auth setup-git`; verify `gh api user --jq .login` is `tarekcmahmoud` | CLI config is under `~/.config/gh`; auth defaults to the system credential store, with plaintext fallback if unavailable. Preserve both config and keyring. Do not distribute Tom's token |
| Git identity and repository | Tarek accepts the private repo invitation; ownership transfer is a later GitHub action Tom already intends | Preloaded `/etc/nixos` snapshot is usable before GitHub login. Keep a working clone owned by Tarek for future changes; root system records exact installed source/revision |
| Google Chrome | Native Chrome sign-in, first account step | Persist `~/.config/google-chrome` plus keyring. Sync authorizes data/extensions separately from the OS image |
| Cloudflare Wrangler | Browser OAuth in Tarek's Chrome; modern versions optionally support device flow and OS keyring | Stable26.05 currently packages Wrangler4.93.0, whose inspected auth source uses writable `config/default.toml`. Keep it0600 on encrypted root. Current docs describe `--use-keyring` and `--device`; verify or update the leaf package before using newer flags |
| Claude Code | Tarek's own `claude auth login` or `/login`, in the correct account root | Linux credential file is writable `~/.claude/.credentials.json` mode0600; `CLAUDE_CONFIG_DIR` relocates the account root. Preserve its mutable state. Do not repeatedly restore an old OAuth snapshot during activation |
| DSH | Own profile/account sign-in, provider credentials loaded at runtime | Preserve DSH-owned `~/.dsh` and chosen account/profile roots; Nix supplies policy through patch overlays and plugins. Home Manager must not own mutable profile files that DSH replaces by rename |
| Provider API keys | Provision only Tarek's own keys; encrypt to his host/recovery identities | agenix ciphertext may live in the repo; decrypt to runtime paths and pass paths to wrappers. Keep plaintext out of derivation arguments, Git, image and logs |
| Tailscale | Own account enrollment on the physical Mac | `/var/lib/tailscale`; retain on normal updates. Re-enroll after clean reinstall unless a controlled same-device identity restore is intentional; never clone one node's state onto multiple machines |
| SSH host keys | Generate uniquely on the Mac, verify public fingerprint | `/etc/ssh/ssh_host_*`; public key becomes an agenix recipient. A replacement key changes both SSH identity and host-secret decryption eligibility |
| Wi-Fi | NetworkManager prompt on installed system | `/etc/NetworkManager/system-connections`, root-only; these are mutable private state, not dotfiles |

[GitHub CLI authentication](https://cli.github.com/manual/gh_auth_login), [Claude credential storage](https://code.claude.com/docs/en/authentication#credential-management), [Wrangler current login/keyring/device options](https://developers.cloudflare.com/workers/wrangler/commands/general/), [Wrangler keyring-required environment option](https://developers.cloudflare.com/workers/wrangler/system-environment-variables/), [Wrangler4.93.0 actual storage source](https://github.com/cloudflare/workers-sdk/blob/wrangler%404.93.0/packages/wrangler/src/user/user.ts).

Current Wrangler can store an encrypted `default.enc` file with its encryption key in OS Secret Service. `CLOUDFLARE_AUTH_USE_KEYRING=true` makes missing keychain support fail rather than downgrade. That is a worthwhile leaf upgrade after validating the shipped version and its new dependency. It does not justify setting a flag that stable4.93.0 does not implement. The current NixOS package pin is [here](https://github.com/NixOS/nixpkgs/blob/f1e5c356f35d07e7b71a6b5e6c9338e0b029e0c0/pkgs/by-name/wr/wrangler/package.nix).

Tom's current configuration already demonstrates two patterns worth retaining: agenix runtime delivery for static API keys, and copy-once to writable state for CLIs that refresh their own credentials. It also records why Claude OAuth seeding was removed: an old encrypted token snapshot repeatedly replaced a valid newer login after a credential file went missing. Tarek should inherit the working persistence principle, not stale token snapshots or Tom's account credentials. Local implementation evidence: `modules/secrets.nix`, `home/dsh.nix`, and `home/antigravity-accounts.nix` in Tom's dotfiles; no secret contents were inspected.

Keep the normal persistent encrypted filesystem initially. An encrypted backup of mutable application state plus host/recovery keys is distinct from the Git dotfiles backup. Rebuilds preserve state automatically; a full reinstallation does not. Restoring arbitrary OAuth snapshots also cannot promise they remain valid: refresh-token rotation, server revocation or expiry can require fresh authorization.

## Qualification before calling the image ready to flash

1. Build the exact target closure and ISO using pinned sources. Check the actual build host has at least25GB free before Nix builds; use the existing compute route, never a NAS compile fallback.
2. Verify the ISO contains the expected target closure, source snapshot, checksum metadata and all necessary packages. Its installer must use that exact closure path.
3. Run a disposable VM installation with networking detached. Prove there is no download/build step, bootloader is installed, LUKS unlock and password login work, and Chrome/Kitty/Claude/DSH are present after first boot. Use a synthetic Apple ESP fixture for retention checks; this proves filesystem behavior, not Apple firmware behavior.
4. Verify a wrong model, USB target, partition path, mounted target, missing firmware, missing backup or unexpected partition layout aborts before data changes. Exercise cancellation and interrupted-install recovery in the disposable VM, never against a live runtime.
5. On the real Mac, first boot the USB without installation. Capture the model, SSD layout, kernel, GPU, Wi-Fi and input facts and check disk-unlock keyboard support. The image can be completely built in advance; physical hardware acceptance still needs this first live boot.
6. Verify sound at low software volume, webcam, Touch Bar input/rendering and recovery, backlight, fans, battery, power/sleep/wake, Chrome graphics/video, Tailscale reconnect and a remote managed update. Hardware build success cannot replace these checks.
7. Publish the qualified private image artifact and checksum with the exact source commit and flashing instructions. No personalized T1 files, credentials or enrolled identities belong in that release.

Supplied source scaffolds pass Nix parser, Bash syntax and ShellCheck0.11 checks. They have not been executed against any disk or booted in a VM in this subtask. The parent owns full image integration, build and installation qualification.
