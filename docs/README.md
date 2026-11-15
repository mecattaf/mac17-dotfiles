# Set up Tarek's Mac, one phase at a time

These guides are for **Tarek Mahmoud's 15-inch 2017 MacBook Pro,
MacBookPro14,3 (A1707)**. The prepared system contains the desktop and programs.
“Dotfiles” means this repository: the settings and source code used to build it.

**Before anything else:** keep this guide and your personal AI conversation
open on a phone or another computer. Erasing macOS will close this Mac's chat.
Confirm that your existing file backup is readable from another device.

| Order | Guide | Finished when |
| --- | --- | --- |
| 1 | [Prepare and download](01-prepare-download.md) | Backup and instructions are accessible elsewhere; verified USB boots. |
| 2 | [Install](02-install.md) | Prepared installer completes; installed system reaches login. |
| 3 | [First login and remote help](03-first-login-management.md) | Wi-Fi, Chrome, your accounts and Tom's remote access work. |
| 4 | [Start free AI](04-free-ai.md) | Your chosen free assistant returns a real reply. |
| 5 | [Check the Mac and contribute](05-verify-and-contribute.md) | Physical checks are recorded and a small design contribution is ready. |

**Who does what:** Tarek operates the Mac and enters his passwords. His personal
AI explains the next step and checks the reported result. Tom supplies the
prepared download, verifies remote access and manages system changes.

**Validated on 15 November 2026:** the image is built with Linux 7.3.4.
All 46 integrated checks, a complete offline installation and an EFI USB boot
have passed in disposable VMs. Physical checks on Tarek's Mac remain pending.
[The latest release](https://github.com/mecattaf/mac17-dotfiles/releases/latest)
has the verified download link. If that link is missing, publication is still
in progress: stop at phase 1 and wait for Tom.

## Give this to your personal AI

Copy the following prompt, then supply this README and only the current phase:

> Guide me through these instructions one action at a time. Start by asking
> which phase I have completed and what screen I see. Explain unfamiliar words
> briefly. Use the supplied commands exactly, replacing a placeholder only
> after checking my actual device. Wait for the result before the next action.
> Check each definition of done. Do not mark an action complete just because
> I opened an app. If a stop condition appears, stop and help me send Tom a
> short description. Never bypass the installer checks, improvise disk erasure,
> enable paid billing, or request passwords, API keys, OAuth codes or private
> keys in chat. Tarek types secrets only into the relevant native app.

After each phase, keep a short checkpoint in your chat: **phase completed;
observed result; unresolved issue; next phase**. Keep account secrets out of it.
Use [START-HERE](START-HERE.md) for the compact overview. Read the research
folder only when Tom needs to investigate a specific problem.
