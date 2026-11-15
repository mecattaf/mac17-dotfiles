# mac17 dotfiles

This is Tarek's independent MacBookPro14,3 system. Account state and device
identities belong to Tarek. Keep credentials, personalized T1 firmware and
private keys out of Git, the Nix store and the ISO.

Build and test on the designated NixOS builder. On Tom's fleet that is
strix-coordinator; check at least 25 GiB free before every Nix build. Runtime
tests use target `~/.local/bin/runtime-test -- command args...`. Never test
destructive installer operations on a real disk or a live user's runtime.

Keep the selected Domicile SDK and engine together. Imagine owns the window
state and actions; the Touch Bar must not invent another window manager.
Preserve vendor licenses and provenance. No Vim-only user interactions.
