# 5. Check the Mac, keep recovery, and contribute

**Tarek tries the physical controls. Tom records failures and manages fixes.**
Software/VM checks have passed; these real-device checks remain necessary.

1. Copy the USB's `mac17-efi-...` firmware-backup folder to a safe private backup
   location. Ask Tom for help opening `MAC17SAVE` if needed. Confirm both copies
   exist before erasing or reflashing the USB. The folder belongs to this Mac;
   do not commit it to GitHub.
2. Check these items one at a time. Record **passed**, **failed**, or **not
   tested**, plus a short observation. Do not treat missing tests as passes.

   | Check | Pass means |
   | --- | --- |
   | Keyboard and trackpad | Typing, clicking, scrolling and pointer movement work. |
   | Display | Chrome and Kitty are readable; brightness controls work. |
   | Wi-Fi | Websites load and the saved network reconnects after a restart. |
   | Touch Bar | Esc, brightness, quiet volume and the Fn/function row respond. |
   | Audio | Quiet speaker output, headphones and the microphone work. |
   | Camera | Chrome can show a camera preview after you grant permission. |
   | Power and cooling | Charging is recognized and the fans behave normally. |
   | Lock and login | Command ⌘ + Control + L locks; your password unlocks. |

3. Check a normal restart only when you are ready. Confirm disk unlock, login,
   Wi-Fi, Chrome and saved assistant state still work. **Sleep is disabled**
   until Tom has tested GPU/T1 resume on this Mac. Use lock or shutdown; do not
   enable sleep as a troubleshooting shortcut.
4. Keep your disk passphrase, login password and service recovery codes in
   your own password manager. With Tom, arrange an **encrypted backup** of
   local account state: Chrome plus its login keyring, DSH and Antigravity,
   GitHub/Wrangler logins and the Mac's SSH/network identity. Record the backup
   location and a successful recovery check; never send the secrets to your AI.
   If that backup is not ready, record it as unfinished. Normal updates keep
   these accounts; reinstalling without a backup means signing in again.
5. Create a small design change with your assistant. A useful first task is
   improving one Imagine onboarding sentence or one clearly named screen.
   Keep the change in a branch and review it together before changing the
   running desktop. Your system settings are in `mac17-dotfiles`; shared Imagine
   source is in [agency-agency/imagine](https://github.com/agency-agency/imagine).
   Ask Tom to establish the first checkout/build workflow; do not edit generated
   files under `/nix/store` or run random rebuild instructions from another setup.

**Done:** recovery copies are retained; each hardware check has a recorded
result; Tom knows the failures; and account-backup status is recorded honestly.
A design contribution is optional and need not delay using the Mac.

**Stop if:** audio, input, display, cooling or boot becomes unreliable. Record
what you did and the observed result, then contact Tom. Keep the installer USB.
Do not reinstall or overwrite account state as a first troubleshooting step.

For later reference: [everyday shortcuts](START-HERE.md#everyday-controls),
[display preferences](retina-display.md), [DSH accounts and updates](dsh-runtime.md).
Normal system updates preserve writable account state. Reinstallation requires
an encrypted personal-state backup or fresh sign-ins; dotfiles alone do not
contain your account logins.
