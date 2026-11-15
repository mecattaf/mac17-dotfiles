# Hardware build validation

Validation date: 15 November 2026. All compilation ran on the compute host. Runtime-sensitive command checks and upstream fixture tests used the target's `runtime-test` wrapper. No MacBook was connected and no real T1, audio module, Wi-Fi module, PAM configuration or desktop session was activated.

## Current target

- Nixpkgs: `d5cc6833999746cffdfe0598f7bc801a57b887a9`.
- Kernel package set: `linuxPackages_latest`, resolving to stable `7.3.4`.
- Pomona: `2ef95b5852b257a9eadb46ba01d3260ead0c84ab`, version `0.11.1`.
- Apple CS8409 patches: `1931615d723899f64b352e9e7ed2368c21c49728`, the 14 November mutex implementation.
- Optional full-pixel T1 drivers: react-drm `b9b1cae3f039dc1d64afefdc1a40955815902526`, with the native Linux 7.3 atomic callback type adaptation.

## Results

| Check | Result and scope |
| --- | --- |
| Native Pomona derivation | Built successfully against the current Nixpkgs input. C/libusb helper, source libraries and Python daemon are in the store. |
| Native CS8409 derivation | Built successfully for Linux 7.3.4. `modinfo` confirms matching vermagic and HDA/scodec dependencies. |
| Optional full-pixel T1 kernel derivation | Built successfully for Linux 7.3.4. `modinfo` confirms both T1 `05ac:8600` and T2 `05ac:8302` aliases and matching vermagic. This package is not enabled with the Pomona profile. |
| Pomona command | `pomona version` reports 0.11.1 under runtime isolation. |
| Invalid firmware input | The native C helper's `--dry-run` rejects a deliberately invalid local sample without opening a T1. |
| Declarative ownership | `pomona audio fix` exits 2 with the NixOS management instruction, before upstream's DKMS/package code. |
| Upstream source fixtures | 282 shell assertions passed: 40 core, 136 Wi-Fi, 57 audio, 14 sleep and 35 history. Python suite: 145 tests, seven skipped, remaining tests passed. |
| Actual laptop acceptance | Pending: boot, wireless association/bands, quiet audio and microphones, camera streaming, fans/power, Touch Bar input/display, lock/logout and sleep/wake. |

The fixture suite assumes ordinary-distribution `/bin/bash` shebangs for its generated mock executables and ambient compiler/make/Python tools. The first attempts exposed those missing NixOS test-environment assumptions. The final run supplied explicit tool paths and changed only fixture mock shebangs to the target's existing Bash. No production behavior was changed to make the suite pass. The fixture runner's optional C-header step was skipped; the native C helper itself was compiled and smoke-tested separately.

The first Linux 7.3 driver attempts also exposed real source-port issues: the React donor used the older DRM atomic transaction type, and copying every header from the audio donor overwrote the newer kernel's own `cs8409.h`. The final implementations follow the matching current kernel callback types and copy only the Apple helper headers. Those errors were fixed rather than suppressed.

## Reproducible outputs

These store paths are the successful current builds; they are architecture/input-derived outputs, not device identifiers:

```text
/nix/store/vdmq45qkgivdljnap6c4yf3w97lhmnn1-pomona-0.11.1
/nix/store/hvvq1ay37fhg3l9xpjv1zsb4psjda0mv-snd-hda-macbookpro-0-1931615-7.3.4
/nix/store/xajymbrzxgwvkckff5r819adsxyhyhlr-react-drm-t1-kernel-0-b9b1cae-7.3.4
```

Earlier builds against Linux 6.18.63 established compatibility with an older LTS source tree. They are superseded for this installation by the stable 7.3.4 results above.
