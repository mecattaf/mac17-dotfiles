# MacBookPro14 3 hardware and Touch Bar

The installation targets the 15-inch 2017 Intel MacBook Pro with the Apple T1. Pomona can run natively on NixOS: its T1 boot path needs a small C/libusb executable, Bash and a Python mode daemon. Runtime Debian packages, DKMS and a GNOME session are not prerequisites for that path. Wi-Fi and sound are supplied declaratively alongside it.

The current system target is the latest stable kernel selected by the locked Nixpkgs input: Linux 7.3.4 at `d5cc6833999746cffdfe0598f7bc801a57b887a9`. Release candidates are outside this target. Earlier Linux 6.18.63 builds were exploratory compatibility checks, not the shipped target.

## The native hardware implementation

| Part | Implementation | Source pin |
| --- | --- | --- |
| T1 startup, fixed Touch Bar strips, camera and light sensor discovery | `pkgs/pomona.nix` and `modules/macbookpro14-3.nix` | [Pomona 2ef95b5](https://github.com/MarcoDiGioia/Pomona/tree/2ef95b5852b257a9eadb46ba01d3260ead0c84ab) |
| Wi-Fi BCM43602 | Checksum-pinned board template, unique per-machine address generated before `brcmfmac` loads; NetworkManager association settings | [Pomona's source and provenance](https://github.com/MarcoDiGioia/Pomona/blob/2ef95b5852b257a9eadb46ba01d3260ead0c84ab/lib/wifi.sh) |
| Internal speakers/headset path, CS8409 | Native external kernel module compiled from the selected kernel's own private/public HDA source and current Apple patches | [snd_hda_macbookpro 1931615](https://github.com/davidjo/snd_hda_macbookpro/tree/1931615d723899f64b352e9e7ed2368c21c49728) |
| Keyboard/trackpad before login and encrypted-disk unlock | In-tree `intel_lpss_pci`, `spi_pxa2xx_platform` and `applespi`, explicitly included and loaded in initrd | [Original SPI driver's requirements](https://github.com/roadrunner2/macbook12-spi-driver) |
| Fans and light sensor | Native NixOS `mbpfan` and `iio-sensor-proxy` integration | Existing NixOS modules |
| Full-pixel Touch Bar driver candidate | Optional `pkgs/react-drm-t1-kernel.nix`, with the Linux 7.3 DRM API port | [react-drm b9b1cae](https://github.com/dev-muhammad-adel/react-drm-for-touchbar/tree/b9b1cae3f039dc1d64afefdc1a40955815902526) |

The audio upstream changed its default locking implementation on 14 November 2026. The native package follows that current source, rather than silently treating Pomona's older September audio pin as the latest version. The driver maintainer still identifies microphone/headset and suspend issues; compiling the driver does not settle those physical behaviors. [Current maintainer commit](https://github.com/davidjo/snd_hda_macbookpro/commit/1931615d723899f64b352e9e7ed2368c21c49728).

The Wi-Fi template has SHA-256 `fbce9f8987759eeac12e36d72637d080945157a95c66c29ce82dbc9caa1b18a1`. It is fetched during image construction. Its original author/licence are unknown; that provenance is recorded by Pomona, and the file is not copied into this Git repository. The installed machine never uses the template's shared address. Its own stable locally administered address is generated from its private machine identity without printing that identity. The module does not hardcode a country: the owner's actual regulatory location belongs in onboarding. [Board provenance](https://github.com/MarcoDiGioia/Pomona/blob/2ef95b5852b257a9eadb46ba01d3260ead0c84ab/data/wifi/README.md).

`pomona status --json`, `pomona wifi status --json` and `pomona audio status --json` remain available for Imagine's hardware page. The Nix package rejects the imperative Wi-Fi/audio install and undo commands; rebuilding the declared system owns those changes. Its audio diagnostics recognize a native Nix module without requiring DKMS. This is a port of Pomona's hardware core and diagnostics, rather than its separate GNOME-oriented settings app.

## Preserve this Mac's Apple EFI data

The T1 operating system is stored under `EFI/APPLE/EMBEDDEDOS/` on the Apple EFI partition. Keep the partition and make an external backup of the complete Apple tree, including `combined.memboot`, `FDRData` and `version.plist`. The user's normal file backup and this device-specific firmware backup are separate items. None of those files belongs in Git, a shared ISO, a diagnostic attachment or another Mac's installation.

Pomona reads the firmware from the same machine's preserved partition and boots it into T1 RAM. Its normal path does not rewrite Apple's firmware or personalized data. In the installed system the partition is mounted at `services.mac17Hardware.appleEsp`, default `/boot/efi`. The live installer must mount that partition before asking Pomona to start a T1 that is in recovery. [Pomona's boot sequence](https://github.com/MarcoDiGioia/Pomona/blob/2ef95b5852b257a9eadb46ba01d3260ead0c84ab/docs/how-it-works.md).

## Three different Touch Bar stacks

| Stack | What it provides | What it needs from Imagine | Current evidence |
| --- | --- | --- | --- |
| Pomona and mainline `hid-appletb-kbd` | Firmware-drawn Escape/special-key/F1–F12 strips, Fn swaps, dimming, per-app selection among those strips | Optional focused-app identifier written to the existing per-user `pomona-focus` contract | Maintainer's exact-model reports; native Nix core package; upstream fixtures |
| react-drm for Touch Bar | Arbitrary pixels, React components, sliders, media/tool/app layers; Node renderer with libdrm/Cairo | A Domicile active-window backend and bounded Imagine action adapter; existing backends cover other compositors | Newly merged T1 code, native kernel-module compilation; physical acceptance remains |
| T1Bridge | T1 lifecycle, full-pixel Touch Bar, unprivileged renderer protocol, optional desktop-provider contract, camera/NCM/SEP integration and fingerprint stack | A provider for standard desktop audio/media/display state, then an Imagine renderer | Source-defined IPC and tester reports; NixOS packaging/physical acceptance still required |

These stacks select different T1 USB configurations and drivers. They must be alternatives, not three services enabled at once. Pomona's configuration 1 gives the firmware strips and mainline HID path. The full-pixel alternatives use configuration 2 and a T1-capable DRM driver. A T2-only `tiny-dfr` or the stock T2 DRM matching table is insufficient for this T1.

### Pomona baseline

The fixed-strip baseline is useful immediately: Escape, volume/brightness/media controls and Fn-to-F-keys. Its per-app policy can put F-keys in an editor and normal media keys in Chrome, but it cannot draw a custom "Resume task" button. That requires the full-pixel route.

The mode daemon reads the internal SPI keyboard's Fn event and writes the mainline driver's mode setting. The user's GUI session is not required for those fixed keys, which matters on this model because it has no separate physical Escape key. Imagine should keep normal media-key handling in its existing native actions.

### Full-pixel React route

react-drm's T1 support merged on 12 November. The repository supplies `apple_dfr_cfgsel`, a T1-capable `appletbdrm`, and compatibility `apple_ibridge` source. Its installer explicitly detects NixOS and leaves native packaging to NixOS; no `install.sh` is run by this project. [T1 installer/source](https://github.com/dev-muhammad-adel/react-drm-for-touchbar/tree/b9b1cae3f039dc1d64afefdc1a40955815902526/system/t1-touchbar-display).

The native candidate installs modules in the Nix generation's `updates/` tree. On Linux 7.3 it follows the matching in-tree DRM atomic callback types (`drm_atomic_commit`) rather than suppressing compiler errors or casting incompatible pointers. The same source had already compiled on Linux 6.18 without that version-specific adaptation.

The Touch Bar DRM/input devices must be assigned to `seat-touchbar`, so Domicile does not discover a second main desktop monitor. The renderer's DRM/input permissions should be scoped to those devices, rather than broadly granting raw access to every keyboard. The upstream direct-renderer architecture uses more raw device access than T1Bridge's broker; that difference matters when choosing the long-term integration.

The renderer is not another browser engine: it uses a custom React reconciler, Yoga layout and Cairo/libdrm. Its existing GUI preview is useful to a designer, but a working preview is separate from real T1 display/input/lifecycle acceptance. Its active-window store has a small `ActiveWindowBackend.start(push)` interface; add a Domicile source there using Imagine's authoritative focused window/app identity. Do not query every compositor as the normal Domicile path. [Backend interface](https://github.com/dev-muhammad-adel/react-drm-for-touchbar/blob/b9b1cae3f039dc1d64afefdc1a40955815902526/linux-touchbar-control-center/lib/activeWindow/types.ts).

### T1Bridge as the stronger integration boundary

T1Bridge's current source is a more structured candidate for the long-term hardware boundary. Its root service owns the Touch Bar DRM device and exposes `/run/t1bridge/touchbar.sock` as a bounded Unix `SOCK_SEQPACKET` protocol. It checks kernel peer credentials, group membership and the active local graphical session. An unprivileged renderer negotiates dimensions, submits sealed shared-memory pixel buffers, receives bounded touch/Fn input and requests a small enumerated set of hardware operations. The root broker receives no shell command or user-supplied executable path. [Renderer IPC](https://github.com/standardagents/t1bridge/blob/81cbdf81026a16e02f0bea74735c6b029a8ffae2/docs/interfaces.md).

A user chooses a custom renderer at `${XDG_CONFIG_HOME}/t1bridge/renderer`. If that process exits, the supervisor falls back once to the built-in renderer. T1Bridge's desktop provider contract already covers volume, mute, media transport, brightness feedback and display blanking. Imagine can implement that provider with its existing actions and state, without inventing a second window manager or exposing a generic executor.

Its source currently includes Rust/C services, custom configuration-selector/DRM/NCM/camera kernel modules and a matched libfprint/fprintd pair for fingerprints. Its architecture docs and package metadata do not always describe the same dependency generation; package the checked source and active build recipe, not a prose dependency claim alone. The current repository's stable renderer/desktop contracts are the relevant reuse surface. [Active package recipe](https://github.com/standardagents/t1bridge/blob/81cbdf81026a16e02f0bea74735c6b029a8ffae2/packaging/arch/t1bridge/PKGBUILD).

Touch ID is no longer accurately described as universally unavailable on T1 Linux. T1Bridge documents successful enrollment on this exact model, following private T1-link/xART setup, with broader model coverage still unconfirmed. That is an optional port/qualification project; it is not part of the Pomona baseline. Use the matched fingerprint library and daemon and preserve a password path for every PAM consumer. Its experimental online recovery is not a substitute for preserving working EFI data. [Model status](https://github.com/standardagents/t1bridge/tree/81cbdf81026a16e02f0bea74735c6b029a8ffae2#supported-hardware), [Touch ID boundary](https://github.com/standardagents/t1bridge/blob/81cbdf81026a16e02f0bea74735c6b029a8ffae2/docs/touch-id.md).

## Useful Imagine Touch Bar behavior

These are proposed product behaviors, using existing app/desktop authority rather than creating another task/session store:

| Context | Touch Bar controls |
| --- | --- |
| Always available | Escape; brightness; volume/mute; media; explicit fallback to F1–F12 |
| Imagine navigation | Named workspaces, Finder, task switcher, help; active workspace indicated |
| Chrome | Back/forward, new tab, address/search, find, zoom, browser media; labels follow normal Chrome shortcuts |
| Kitty | New terminal, terminal/session chooser, copy/paste/search; use the existing local Kitty/Domicile integration |
| Claude Code/DSH | Current session state, open the relevant chat, explicit stop/cancel, show pending approval in the real UI; no credentials or invented approval authority on the bar |
| Designer workflow | Capture region/window, open design workspace, toggle a preview; context follows the actual focused app |
| Onboarding | Back/Continue/Open Chrome/Help, plus live hardware test feedback; keyboard/trackpad alternatives always available |
| Locked desktop | Only intentional hardware controls; clear browser/task titles and private context |

Use Domicile/Imagine's real reducer and typed action dispatcher for navigation and app actions. `dsh-domicile` remains a read-only introspection boundary; a Touch Bar button must not silently turn it into generic remote execution. Agent session identity, desktop identity and window identity remain distinct.

Implement the integration incrementally: first add the standard T1Bridge desktop provider or react-drm Domicile focus source; next test a renderer with permanent Escape/F-key fallback; then add Chrome/Kitty/workspace controls; finally connect DSH status and deliberate actions through their existing owners. Do not make the first installation depend on a novel renderer to type Escape or connect Wi-Fi.

## Hardware acceptance on the actual laptop

The image/build work does not substitute for these physical checks:

- Cold boot from USB and installed disk; internal keyboard/trackpad work before login and at any disk-unlock prompt.
- Preserved Apple EFI files remain readable; T1 becomes `05ac:8600`; no generic firmware from another Mac is used.
- Escape, Fn/F1–F12, brightness, volume, media and dim/wake function across login and logout.
- Wi-Fi joins the owner's network, shows usable 2.4/5 GHz bands for the actual regulatory location, reconnects after reboot and does not use the shared template address.
- The loaded CS8409 module resolves to the generation's `updates/` module and matches the booted kernel. Test quiet PipeWire output, both speakers, headphones and both microphones separately. Direct `hw:0,0` playback has no normal volume control and is unsuitable for this first test.
- Camera captures an actual stream in Chrome/WebRTC; a `/dev/video` node alone is insufficient.
- Fans respond under normal load; battery charging/state is sane; idle power is measured under stated conditions.
- Locking, display blanking, lid behavior, shutdown and reboot work. System suspend remains opt-in until repeated attended suspend/resume passes on the chosen GPU/kernel/T1 profile.
- Before selecting a full-pixel profile, verify the Touch Bar's isolated DRM seat, process failure fallback, locked-state privacy, touchscreen input, camera coexistence, shutdown and resume.

Do not blacklist the Radeon GPU merely because a donor did: the correct Intel-only path depends on EFI GPU exposure and the machine's actual display path. General GPU/lid/power research is recorded separately from the Touch Bar stack selection.
