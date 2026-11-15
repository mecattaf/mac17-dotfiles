# Ready for daily use

**Target:** Tarek uses Domicile and Imagine as his everyday desktop after
installation and account setup. Tarek enters his own credentials; Tom manages
the system through Tarek's Tailscale account. His personal AI guides one check
at a time using this file and the [phase guides](README.md).

## Finish the account setup

For each row, record **working**, **deferred**, or **not used**. A working
account must pass its check; opening its login page is not enough.

| Account or service | Check before marking working |
| --- | --- |
| Chrome / Google | The intended Chrome profile opens, chosen saved information is available, and the profile remains usable after restarting the Mac. |
| GitHub | GitHub CLI confirms **tarekcmahmoud** and access to `mac17-dotfiles`. Accept both repository invitations. Tom sets the chosen Git commit email in the Nix configuration before the first contribution. |
| Tailscale | This Mac belongs to Tarek's account. Tom accepts the Admin invitation and node share, verifies the SSH fingerprint and makes a real remote connection. |
| Free AI | A selected free route returns a real reply using Tarek's own account, with paid billing disabled. See [phase 4](04-free-ai.md). |
| DSH, if chosen | Tarek saves his own provider credentials through Settings → Models, receives a reply and reopens the same conversation. See [DSH instructions](dsh-runtime.md). |
| Cloudflare | Tarek owns the account and Wrangler identifies it after authorization. Workers AI API access requires its own suitable token; Wrangler sign-in alone is not an inference test. |
| Additional AI providers | Use the [provider guide](free-ai.md), one service at a time. Record an actual successful request or an honest deferred/not-used status. |
| Claude Code | Optional. Connect only if Tarek chooses it. |

Keep recovery codes in Tarek's password manager. Record the encrypted backup
location and recovery check with Tom. A deferred backup stays visibly unfinished.
Repository ownership transfer to Tarek is a separate item on the
[owner checklist](tarek-setup-checklist.md).

## What the dotfiles manage

`mac17-dotfiles` manages installed programs, system settings, desktop defaults
and these instructions. Chrome profiles, keyrings, CLI logins and API keys stay
in native writable storage on the encrypted disk. Normal NixOS updates preserve
that state. Reinstallation needs an encrypted personal backup or fresh sign-ins.

## Definition of done for daily use

- The internal disk boots into Domicile/Imagine after disk unlock and login.
- A normal restart preserves Wi-Fi, Chrome and the chosen assistant account.
- Keyboard, trackpad, display, Touch Bar controls, quiet audio, camera and
  cooling have actual recorded checks from [phase 5](05-verify-and-contribute.md).
- Tom confirms remote management; GitHub confirms the correct account and repo.
- At least one free assistant has answered; every account row has a recorded status.
- Tarek can launch Chrome and Kitty, switch workspaces, lock/unlock and resume setup.

**Stop if** boot, input, display, cooling or account persistence fails. Send Tom
the observed error and the last completed check. Sleep stays disabled until
physical GPU/T1 resume is qualified. Daily readiness is established on this Mac;
the published VM checks establish the installer's preparation.
