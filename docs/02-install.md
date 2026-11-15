# 2. Install the prepared system

**Tarek runs the installer locally. Tom helps identify the internal disk.**
Keep power connected and the guide/chat on your second device. Installation
replaces macOS. Your file backup must already be readable elsewhere.

The desktop and applications are on the USB. Installation does not need Wi-Fi
to fetch them. The prepared USB also has a writable `MAC17SAVE` partition for
the Mac's firmware backup; a second USB is not required.

1. At the live console, run these read-only commands, one at a time:

   ```sh
   lsblk -d -o NAME,SIZE,MODEL,TRAN
   ls -l /dev/disk/by-id/
   ```

   Identify the internal Apple SSD and its persistent `/dev/disk/by-id/` path.
   Have Tom or your AI check the model, size and link destination. It must not
   be the USB or a path ending in `-part1`, `-part2`, etc. If unsure, stop and
   ask Tom. Do not guess a path from another computer.
2. Replace `<your-internal-Apple-SSD>` below with that actual path. The angle
   brackets are placeholders, not text to type. Run the plan command:

   ```sh
   sudo mac17-install --disk /dev/disk/by-id/<your-internal-Apple-SSD>
   ```

3. Read the plan. It must identify this Apple SSD, retain the existing Apple
   EFI partition, and create an encrypted Linux system. EFI is the small boot
   partition containing this Mac's T1 firmware. Keep it. If the plan fails or
   differs, stop; do not use another partitioning command.
4. After reviewing the correct plan, run the same path with `--install`:

   ```sh
   sudo mac17-install --disk /dev/disk/by-id/<your-internal-Apple-SSD> --install
   ```

5. Wait for **Verified EFI backup**. Note the displayed backup folder on the
   USB. Only then, if you intend to replace macOS, type `INSTALL MAC17` at the
   local confirmation prompt. Choose a disk-unlock passphrase and later a Linux
   login password. They have different purposes; remember both privately.
6. Wait for **Installation finished**. Remove the USB, then restart the Mac.
   Enter the disk-unlock passphrase. The installed system should show its login
   screen. Keep the USB and its firmware backup for recovery.

**Done:** the installer reported success and the internal installed system
reached login after the USB was removed.

**Stop if:** a model/disk/firmware/backup check fails, backup space is insufficient,
installation errors, or the installed system cannot boot. Send Tom the exact
error and which step completed. Do not rerun installation, erase EFI, or reflash
the USB containing your only firmware backup. Never send either password.

Next: [3. First login and remote help](03-first-login-management.md).
