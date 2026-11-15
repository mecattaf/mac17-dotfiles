# 1. Prepare the download and USB

**Tarek does these steps.** Tom must first publish the prepared installer.
You need power, a USB stick large enough for the release's stated image size,
and a phone or second computer for this guide and your personal AI chat.

1. On the second device, open these guides and your AI conversation. Confirm
   that you can read a file from your existing personal backup. The USB used
   for installation will be erased; it must not hold your only file backup.
2. Sign in to GitHub as **tarekcmahmoud**. Accept the `mac17-dotfiles` and
   `agency-agency/imagine` invitations if they are pending.
3. Open [the latest prepared release](https://github.com/mecattaf/mac17-dotfiles/releases/latest).
   Use its **Download installer** link. Download and extract the
   **mac17-installer** artifact. It must contain `mac17-installer.iso` and
   `SHA256SUMS`. Do not flash an individual `.part-*` archival file.
4. In macOS Terminal, type `cd `, drag the extracted folder onto the window,
   and press Enter. Then run:

   ```sh
   shasum -a 256 -c SHA256SUMS
   ```

   The line for `mac17-installer.iso` must end in `OK`. This checks that your
   downloaded image matches the publisher's checksum.
5. Open [balena Etcher](https://etcher.balena.io/). Select the ISO, then identify
   and select your USB stick. Check its name and size. Flash and let validation
   finish. This erases the selected USB stick.
6. If macOS calls the flashed disk unreadable, choose **Ignore** or **Eject**.
   Do not choose Initialize. Connect power, restart holding **Option ⌥**, and
   choose **EFI Boot**. Keep the second device available.

**Done:** the checksum passed, Etcher completed, and the Mac reached the
prepared NixOS live console. The internal Mac disk has not been erased.

**Stop if:** there is no published installer link, a file is missing, the
checksum fails, you cannot identify the USB, or EFI Boot does not reach the
prepared console. Tell Tom the exact non-secret error. Do not substitute a
generic NixOS image.

Next: [2. Install](02-install.md).
