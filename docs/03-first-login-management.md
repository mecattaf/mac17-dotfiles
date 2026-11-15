# 3. First login, browser and remote help

**Tarek signs in to his own accounts. Tom verifies management access.**
The Linux username is **tarek**. Use the login password chosen during
installation; the earlier disk-unlock prompt uses the other passphrase.

1. Sign in. Keep the laptop lid open and external monitors disconnected for the
   initial display setup. Imagine is the desktop shell; Domicile manages its
   windows. Open setup with **Command ⌘ + Shift + O** if needed.
2. In the native network controls, choose Wi-Fi and enter its password there.
   It is saved locally and survives restarts. Do not send it to Tom or your AI.
3. Open Chrome with **Command ⌘ + N**. Use Chrome's **profile button** to sign
   in to your own Google Account. Check your bookmarks and saved information.
   Signing in to a Google website alone does not sign in the Chrome profile.
4. If Chrome reports a locked keyring, use **Unlock keyring** in setup and
   create/unlock the login keyring. A keyring is the encrypted local credential
   store. Use your Linux login password; do not make an empty-password keyring.
5. In Imagine setup, connect **your Tailscale account**, which owns this Mac.
   Tailscale provides the private network used for remote help. In its
   [admin console](https://login.tailscale.com/admin/users), choose **Users →
   Invite external users → Admin**. Generate the invitation and send it to Tom
   privately. Then choose **Machines → this Mac → Share** and send him that
   separate sharing invitation. An account invitation and device sharing do
   different jobs; this Mac remains in your account.
6. Connect GitHub through Imagine setup as **tarekcmahmoud**. Accept the
   repository invitation if prompted. Tom transfers `mac17-dotfiles` ownership
   to you separately; signing in does not perform that transfer.
7. Ask Tom to verify the Mac's SSH host fingerprint and a real remote
   connection. “Tailscale connected” alone does not prove remote management.

**Done:** Wi-Fi works, Chrome's correct profile is usable, GitHub setup confirms
the expected account/repository access, and Tom confirms actual remote access.
Optional AI and Cloudflare steps can be completed later.

**Stop if:** the desktop does not appear, controls are unreadable, Wi-Fi fails,
the keyring cannot unlock, the wrong account owns the Mac, or Tom cannot reach
it. Keep the machine running if possible and describe the visible error.
Do not copy Tom's credentials, node identity, or private keys onto the Mac.

Next: [4. Start free AI](04-free-ai.md). Keep the
[account completion checklist](daily-use-and-accounts.md) alongside setup.
