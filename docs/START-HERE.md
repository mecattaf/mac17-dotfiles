# Install your prepared NixOS desktop

This image is for your **15-inch 2017 MacBook Pro (MacBookPro14,3)**.
Your personal file backup is already done. The installer also saves the
Mac's small Apple firmware partition before replacing macOS.

## Download and flash

1. Accept the GitHub invitations for `mac17-dotfiles` and `agency-agency/imagine`
   while signed in as **tarekcmahmoud**.
2. Open [the latest release](https://github.com/mecattaf/mac17-dotfiles/releases/latest).
   Follow **Download installer** in the release notes and download the
   **mac17-installer** artifact. Extract the ZIP: it contains
   **mac17-installer.iso**, **SHA256SUMS** and these instructions. Use this
   prepared image rather than a generic NixOS download. The `.part-*` release
   files are archival pieces; do not flash an individual part.
3. In macOS Terminal, from the extracted folder, run `shasum -a 256 -c SHA256SUMS`.
   Check that the ISO reports `OK`.
4. Open [balena Etcher](https://etcher.balena.io/), choose the ISO, select your
   USB stick and flash it. Flashing erases the USB stick. Use a stick large
   enough for the release's stated image size; 16 GB is recommended.
5. Connect power. Restart while holding **Option ⌥** and choose **EFI Boot**.

Etcher may leave macOS showing an unreadable-disk notification after flashing.
Choose **Ignore** or **Eject**, not Initialize.

## Install

The desktop and programs are already on the USB. A network connection is not
needed to download them during installation.

The live console shows the prepared installer command. It checks your exact
Mac model and Apple SSD, prints what it will keep and replace, and requires
you to confirm locally before removing macOS. **Keep Apple's existing EFI
partition. Do not run a generic whole-disk erase or the ordinary installer.**

The prepared USB also has a writable **MAC17SAVE** partition. The installer
saves and verifies the Apple firmware backup there before erasing macOS. No
second USB drive is needed. Keep this backup: copy it somewhere safe before
you flash or erase this USB again. If the partition is full, the installer
stops; you can instead supply `--backup-dir` on another mounted writable disk.

The two installer commands are:

```sh
sudo mac17-install --disk /dev/disk/by-id/<your-internal-Apple-SSD>
sudo mac17-install --disk /dev/disk/by-id/<your-internal-Apple-SSD> \
  --install
```

The first prints a plan. Use the complete persistent disk path shown on your
Mac; it is not a partition path. The second requests `INSTALL MAC17`, a disk
unlock passphrase and your Linux login password. Tom can help with selecting
the correct paths. Neither password belongs in GitHub or a message to Tom.

After it reports completion, remove the USB and restart. Enter the disk
passphrase, then sign in as **tarek** with your Linux password.

## First desktop session

The setup experience uses this order:

1. **Connect to Wi-Fi.** Enter your password in the native network controls.
   It is stored by NetworkManager and survives restarts. Ethernet can replace
   this step. You do not need to send Tom the Wi-Fi password.
2. **Sign in to Google Chrome.** Open the profile button and sign in with your
   own Google account. Check your bookmarks and saved information. Chrome is
   the first account login on the new desktop. Sync remains your choice.
3. **Start a free AI assistant**, if you want one now. Choose Google
   Antigravity with your own personal Google Account, then confirm after you
   receive a reply. Its launcher disables paid-credit fallback. See
   [the free AI guide](free-ai.md) for other services. Claude Code is optional.
4. **Connect your Tailscale account.** Choose the account that will own this
   computer, then invite Tom as described below.
5. Connect GitHub as **tarekcmahmoud**, then choose your free AI accounts
   in setup. Claude Code is optional. Cloudflare is included for your own utilities.

The Linux login unlocks your encrypted keyring. If setup says it is locked,
use **Unlock keyring** before Chrome sign-in; avoid creating an empty-password
keyring. Account logins are stored on your encrypted system and are preserved
by normal NixOS updates.

## Invite Tom through Tailscale

In your [Tailscale admin console](https://login.tailscale.com/admin/users),
open **Users → Invite external users**, choose **Admin**, generate the invite
link and send that link to Tom privately. This gives him account-management
access; he signs in with his own identity.

To let his existing computer reach this Mac without moving his machines into
your account, also open **Machines → your Mac → Share**, generate a sharing
invitation and send it to him. Keep the Mac enrolled in your own account.
The image's initial management key works only after the network and access
policy allow the connection. Tom will verify the Mac's SSH host fingerprint
before the first managed update.

## Everyday controls

The **Command ⌘ key is Meta** for the desktop. Ordinary app shortcuts use
Control, as displayed in Chrome and the editor. There are no required Vim keys.

| Action | Shortcut |
| --- | --- |
| Open Chrome | Meta+N |
| Open Kitty terminal | Meta+Return |
| Open files | Meta+E |
| Search apps | Meta+Space |
| Focus a window | Meta+Arrow |
| Move a window | Meta+Shift+Arrow |
| Switch workspace | Meta+1 through Meta+0 |
| Clipboard history | Meta+V |
| Screenshot | Meta+Shift+S |
| Lock | Meta+Control+L |
| Resume setup | Meta+Shift+O |

Nano is the terminal editor; the graphical text editor handles ordinary files.
The Touch Bar provides Escape, hardware controls and Fn/F1–F12. Custom rendered
Touch Bar controls are researched separately and can be added through managed
updates after the initial hardware checks.

## Check the Mac together

On the first installed boot, check keyboard/trackpad, Wi-Fi reconnection,
Touch Bar/Fn, brightness, quiet speaker output, headphones, microphones,
Chrome camera capture, charging and fans. Sleep remains disabled until its
GPU/T1 resume path has been tested on this particular Mac; use lock/shutdown
in the meantime. A successful software build does not establish those physical
checks. Keep the USB for recovery.
