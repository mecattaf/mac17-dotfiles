# MacBookPro14 3 NixOS donors and general hardware plan

Research, 15 November 2026. Tarek’s target is the 15-inch 2017 Intel MacBook Pro with T1, MacBookPro14,3. Five actual GitHub Nix configuration repositories were inspected in detail. Four explicitly identify that exact model. The fifth identifies a 2017 MacBook Pro with an AMD discrete-GPU path, which strongly identifies the same 15-inch generation by inference; its text does not spell out MacBookPro14,3. This distinction is preserved below. No fork was counted merely to reach five.

## Five donor configurations

| Repository and inspected commit | Device evidence | Useful learning | What must not be copied unchanged |
| --- | --- | --- | --- |
| [esodesod/nixos](https://github.com/esodesod/nixos/tree/69ee0b781a53a94c873be0e02e69db274d14d521), `69ee0b781a53a94c873be0e02e69db274d14d521` | [`mbp17-01/nixos/hardware-configuration.nix`](https://github.com/esodesod/nixos/blob/69ee0b781a53a94c873be0e02e69db274d14d521/mbp17-01/nixos/hardware-configuration.nix) explicitly says 15-inch 2017 with Touch Bar, MacBook 14,3, A1707 | Preserve the macOS-created Apple EFI partition because it carries Touch Bar firmware. Include the SPI keyboard/trackpad stack early. Build both audio and Touch Bar modules through Nix. Package the BCM43602 board file declaratively. Use PipeWire. | Their ZFS layout, Norwegian/ISO keyboard setting, SSH identities, disk paths, initrd networking, hardware UUIDs and old driver API assumptions are specific to their device. Their configuration comments report an XBOOTLDR black screen, so a separate boot partition is not automatically a proven Apple solution. |
| [wobbier/nix](https://github.com/wobbier/nix/tree/a13858a1d7eaa81f2603b8e936933e23c8b2857f), `a13858a1d7eaa81f2603b8e936933e23c8b2857f` | [`hosts/dankbook/dankbook.nix`](https://github.com/wobbier/nix/blob/a13858a1d7eaa81f2603b8e936933e23c8b2857f/hosts/dankbook/dankbook.nix) explicitly identifies MacBook Pro 14,3 | Separate sound and Touch Bar derivations under host modules. Kernel pinning is part of an external driver contract. BCM43602 board data is included as a firmware package rather than downloaded at every boot. Bound boot generations when using a small EFI partition. | It uses kernel 6.6 and older out-of-tree driver code. Crucially, its committed `hardware-configuration.nix` is a deliberate `throw` placeholder. This is a useful source pattern, not an immediately buildable configuration or evidence that this exact revision is live on a laptop. |
| [archaengel/systemConf](https://github.com/archaengel/systemConf/tree/71607890df8b1e7bbb6626e300fab08bc3278d58), `71607890df8b1e7bbb6626e300fab08bc3278d58` | [`machines/1134-nixmac/configuration.nix`](https://github.com/archaengel/systemConf/blob/71607890df8b1e7bbb6626e300fab08bc3278d58/machines/1134-nixmac/configuration.nix) explicitly says macbook pro 14,3 | Hardware-oriented configuration includes board firmware, early SPI/T1 modules and per-device libinput integration/palm settings. Shows the importance of CPU/thermal policy on this chassis. | It blacklists amdgpu. That is unsafe to transplant before qualifying the Intel EFI/mux boot route: the 15-inch machine may boot with its internal panel attached to the Radeon. Its hand-tuned touch-size thresholds and `acpi_osi=Darwin` are not universal defaults. |
| [gilescope/dotgiles](https://github.com/gilescope/dotgiles/tree/88231102121642b5f2361c88f2a6869d7f24a6ad), `88231102121642b5f2361c88f2a6869d7f24a6ad` | [`README.md`](https://github.com/gilescope/dotgiles/blob/88231102121642b5f2361c88f2a6869d7f24a6ad/README.md) explicitly identifies MacBookPro14,3, 15-inch Touch Bar, T1 | EFI GRUB fallback is configured through `efiInstallAsRemovable`, using `/boot/efi`; fan control, clickfinger/natural scroll and a readable HiDPI console are concrete usability concerns. The author clearly marks unfinished audio and Touch Bar work. | This is historical work, last inspected tip from 2021. Its README lists sound and Touch Bar as TODO; it is not a full hardware solution. Old option names, kernel-latest selection and speculative audio model settings must not be inherited. |
| [rehno-lindeque/wip](https://github.com/rehno-lindeque/wip/tree/009137325b1c554b18a291ff7c7f966a91361fd4), `009137325b1c554b18a291ff7c7f966a91361fd4` | [`my-nixos-configurations/nixos-modules/profiles/macbookpro2017/default.nix`](https://github.com/rehno-lindeque/wip/blob/009137325b1c554b18a291ff7c7f966a91361fd4/my-nixos-configurations/nixos-modules/profiles/macbookpro2017/default.nix) identifies the 2017 MacBook Pro and explicitly handles amdgpu backlight and GPU switching. **Same 15-inch 2017 model inferred, not directly named.** | Strong example of explicit persistent mutable account state: `.config`, Claude/Codex state, SSH keys and application state survive an impermanent home. EFI GRUB removable boot and encryption are separate from application persistence. Remote management is intentionally tied to the tailnet. | Their fixed tailnet IP, password-enabled SSH TODO, external speech services, impermanent-root scheme, custom keyboard mapping, Vim state and historical bootloader conclusion are personal choices. For Tarek, preserve the persistence principle without copying their machine/account identities or a complex filesystem scheme. |

The matrix is five configurations with four directly verified model labels and one strong model inference. It is not five independent demonstrations that every component works on current NixOS.

## How the learning combines

Prepare one target configuration and a complete offline install closure. Use a stable kernel whose external drivers were actually built. Include board firmware, early mainline SPI keyboard support, PipeWire, the selected audio package, the T1/Pomona stack, NetworkManager and the full desktop. The installer must retain Apple EFI firmware and use Tarek-specific fresh host identities. His username, Git identity and accounts are independent of all donors.

For a small original Apple EFI partition, a GRUB EFI loader with kernels/initrds on the Linux filesystem can avoid filling the original ESP with multiple generations of Nix kernels. The installer must match its chosen mount/boot strategy exactly and retain the EFI fallback path. Merely switching bootloader options from another laptop is not validation. This is especially relevant because one exact donor reports an XBOOTLDR black screen.

Donors generally put `applespi`, `intel_lpss_pci` and `spi_pxa2xx_platform` in the initrd’s available modules. For an encrypted installation, ensure the actual SPI stack is loaded before the passphrase prompt; an installed module that is only available later does not make that prompt usable. Preserve the in-tree applespi module and avoid accidentally shadowing it with an old driver bundle.

Keyboard layout is a real device fact. Do not copy an ISO-layout toggle from a Norwegian machine or a Caps/Esc swap from a developer’s config without checking the physical keyboard. Tarek does not use Vim. A visible Escape control and plain Nano default are useful while keeping ordinary Chrome shortcuts intact.

## Graphics, sleep and external displays

A major 15-inch-specific issue is which GPU owns the internal panel at boot. The Mac has Intel integrated graphics and Radeon discrete graphics. A configuration that simply blacklists Radeon can leave the screen unavailable if EFI routed the panel to it.

Two exact-model primary sources clarify the tradeoff:

- [mythopoeic/macbookpro14-3-linux](https://github.com/mythopoeic/macbookpro14-3-linux/tree/5b507f5f3206fc7ecdaff06cf4e7d55d0eac5466), commit `5b507f5f3206fc7ecdaff06cf4e7d55d0eac5466`, documents actual refusal of live mux switching both during a desktop session and early boot. Its `docs/FINDINGS.md` and `gpu/README.md` distinguish reducing Radeon idle clocks from actually turning the Radeon off. It also documents real USB-C controller power/hotplug and thermal behavior. This is Ubuntu hardware evidence, not Nix dotfiles.
- [paskaz/mbp143-linux-suspend-fix](https://github.com/paskaz/mbp143-linux-suspend-fix/tree/b7d13f8eccfc6dfbe00898e399baaca4f0b53fc2), commit `b7d13f8eccfc6dfbe00898e399baaca4f0b53fc2`, reports a tested Intel-panel boot path: EFI `gpu-power-prefs`, an apple_set_os/rEFInd spoof, Radeon removal and PCI bridge d3cold control. It explicitly trades working internal-panel suspend for the loss of external video ports attached to Radeon. Its installer is Ubuntu-specific and was not executed.

These reports are compatible: a successful firmware-selected Intel boot is different from attempting a live mux change after Linux already owns the panel. They do not establish that every kernel or every unit behaves identically.

For the initial image, retain the normal GPU path and preserve a visible working desktop. Qualify a dedicated Intel/suspend boot configuration separately if it is part of the deliverable, including a known recovery entry and an explicit external-display tradeoff. Read actual connected DRM outputs and drivers after boot; do not make acceptance depend on fixed `card0/card1` ordering.

Until a physical sleep/wake qualification passes on Tarek’s laptop, a lid action that locks and blanks without suspend is an explicit temporary behavior. The onboarding should say what it does. It must not claim successful suspend because `systemctl suspend` returned or the machine disappeared from Tailscale. Verify resume of the panel, keyboard/trackpad, camera/Touch Bar, audio, Wi-Fi, Bluetooth and remote management.

## Thermal, power and dock details

Enable the Apple SMC path and a deliberate fan-control choice. The primary exact-model thermal report above shows why copying another person’s fan temperatures and polling interval can produce either surging noise or delayed cooling response. Its own measurements apply to its CPU and cooling state. Do not import hardcoded fan minima/maxima or CPU power caps without observing Tarek’s unit.

Choose a coherent CPU power-policy owner. The donors use different combinations of thermald, auto-cpufreq and other policies; merging every switch from every repository does not create a better laptop. Keep thermal protection, fan control and user-selectable power policy understandable.

On USB-C/Thunderbolt, test storage, charging, Ethernet and displays on both sides of the laptop. The exact-model hardware report identifies controller runtime power state as a cause of apparently dead hotplug. A generic global PCI power tweak can hide the distinction; any workaround should target the actual affected controller and be justified by the test. Do not globally disable PCI power saving to satisfy a broad inherited recipe.

Use Retina-appropriate desktop and console sizing, with actual connector identities discovered on the Mac. A reasonable initial 2x scale can be adjusted by the user. Do not copy Tom’s two Zenbook panel identities, external-display assignments or per-panel temperature values.

## Other repositories examined and correctly excluded from exact-model count

- `BalrajSinghGidda/nixos-dotfiles`: its mac-btw host explicitly says MacBookPro14,1; a useful audio derivation but the 13-inch non-Touch-Bar sibling.
- `quesadx/dotfiles`: macbook-pro-2017 audio module explicitly targets 14,1, despite the generic folder name.
- `cameronraysmith/vanixiets`: pyrite’s very detailed hardware inventory explicitly identifies 14,1 and BCM4350. Its firmware assumptions are not the T1 model’s BCM43602 needs.
- `solrey3/Nix` and `solrey3/nix-config`: charlie explicitly identifies 2017 13-inch MacBookPro14,1.
- `fvla/nixfiles`: MBP142 profile is the 13-inch T1 sibling.
- `life00/dotfiles`, commit `0fcde51a89d6535760fdf670b8a8aeea22c1c60c`: has a real mb2017 NixOS host and a useful current CS8409 package, including the newer `build/hda/codecs/cirrus` module output path, but no exact model evidence was found. Good packaging source, not counted as exact-device proof.
- `Indyandie/nizu`: its mb-pro module explicitly identifies MacBookPro11,5 with a Haswell CPU and older Radeon, despite sharing BCM43602.
- `petertriho/nix-config`: MBP15-I7 explicitly identifies MacBookPro15,1 and Radeon Pro 560X, a T2-generation Mac.
- `anntnzrb/_nixrice`: a search hit for i7-7700HQ describes an ASUS laptop, not a Mac.
- `sporto/nixpkgs`, `theinhumaneme/nixos` and several MBP14 hits are macOS/nix-darwin configurations rather than NixOS hardware configurations.
- `scalavision/dotgiles` is an old fork of gilescope’s exact-model repo. It was not counted as an additional independent donor.

No disk mutation, EFI variable write, module unload, compositor test, suspend, remote account operation or upstream installer was run during this audit. All relevant donor paths and metadata were fetched read-only through the authenticated mecattaf GitHub CLI. Source files in the scratch audit are evidence, not an instruction to vendor an entire personal configuration or publish its account-specific settings.
