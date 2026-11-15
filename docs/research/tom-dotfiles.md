# Lessons from Tom's dotfiles for Tarek's single device

The comparison uses `mecattaf/dotfiles` at
`435e61f084fce5f4892dad608703eb10a5ad8d49`, inspected on 15 November 2026.
Tarek's configuration is independent. The transferable pieces are ownership
and lifecycle choices, rather than Tom's hostnames, accounts or hardware facts.

## Source and package ownership

Tom separates base Nixpkgs from rapidly changing agent programs. The
`llm-agents.nix` catalog builds against its own Nixpkgs and supplies a signed
binary cache; following the fleet Nixpkgs pin would discard many substitutes.
His current `home/agent-tools.nix` uses an explicit allowlist after an earlier
install-everything experiment became unnecessarily broad. Tarek starts with
Claude Code and DSH. More agent tools can be added deliberately.

The current upstream catalog's export changed: it exposes
`packages.<system>` and `overlays.shared-nixpkgs`, while older integration
comments still describe `overlays.default`. The fresh configuration uses the
actual exported package set directly. This was caught by evaluation rather
than silently installing an older replacement.

The desktop is a matched Domicile source/SDK and engine pair. Tom's
`modules/domicile.nix` checks the evaluated configuration and bundles every
relative Imagine dependency together. An immutable source stamp prevents an
Imagine-only update from reusing a stale bundle. Tarek retains that checking
and source-stamp pattern. Imagine itself is the shared Manganese-derived shell;
machine-specific entries select user controls and device facts.

## A useful desktop without copied device facts

Tom's `home/dot_config/domicile/domicile.tsx` names two Zenbook panels, a 5K
external display, per-output workspace homes, fonts and temperature choices.
Those values do not describe Tarek's single Retina panel. His configuration
uses native output discovery and an independently chosen readable setup.

The Imagine reducer owns workspace/window/layout state. Its Stage owns final
geometry. Touch Bar navigation and onboarding must call those existing actions
instead of inventing a second layout model. The `dsh-domicile` snapshot protocol
keeps agent-session identities, desktops and windows distinct, omits titles/URLs
by default and respects lock state. Those are the useful boundaries to retain
when Tarek starts contributing.

Tom's browser routing deliberately opens web links in ordinary Google Chrome,
preserving the real personal profile rather than making Domicile's engine a
second personal browser. Tarek follows the same native Chrome route. His
application Control shortcuts remain available: the fleet's global Control+N
launch shortcut is not copied. Arrow navigation replaces required Vim chords;
Nano and the graphical text editor replace Neovim defaults.

`home/agency-kitty.nix` has important local-versus-remote distinctions: native
terminal transport, explicit socket-only control, prompted clipboard reads,
session identity checks and an independently qualified editor path. Tarek is
a single-device user initially. A plain local Kitty is the appropriate first
entrypoint; NAS-oriented host routing and the Neovim helper are not copied.

## Credentials and writable settings

`modules/secrets.nix` demonstrates why credentials do not belong in immutable
dotfiles. Application refresh tokens are copied to writable state when a
restore is actually needed. Symlinking OAuth files into the Nix store breaks
refresh. A stale Claude seed was explicitly retired after it kept restoring
an old token. Tarek signs in once; rebuilds preserve his writable login state.

The same distinction appears in `home/agent-tools.nix` and
`home/claude-settings.py`: settings remain user-editable and model/effort
choices are not reset on activation. Skills/rules may be delivered as narrow
links, but `.claude`, `.dsh` and the whole Chrome profile are real writable
directories. Tarek's initial image contains no Tom credentials, account
cookies, provider keys or pre-authorized Tailscale node identity.

Chrome and current GitHub CLI can use Secret Service. On Tom's Zenbook,
`modules/keyring-autounlock.nix` solves autologin with TPM-sealed material.
The T1 Mac has no equivalent standard TPM2 path. Its fresh setup uses a normal
password login and PAM-unlocked GNOME Keyring before the Chrome-first account
step. Keyring creation/unlock must have a visible recovery action.

Rebuild persistence, backup and reinstall are different operations. A rebuild
leaves mutable state alone. A recovery backup needs the Chrome profile **and**
keyring, GitHub credentials/metadata, Claude/DSH state, Wrangler state, SSH
identity, NetworkManager connections, Tailscale state and the host decryption
identity. Backups must be encrypted and restore-tested. Do not copy a live
Tailscale identity to two simultaneously running machines.

## Agent lifetime and management

`modules/dshd.nix` and `docs/dshd-nas.md` separate a durable native process
from its terminal/browser frontend. Installing a service template starts no
user conversation. A running instance keeps its declared release through a
configuration switch; choosing a new release for a future start differs from
restarting an existing session. Tarek receives the reusable dshd mechanism
with his own writable DSH home and accounts.

Tom's `home/dsh-master.nix` renders separately owned transport/profile folders
and keeps credentials outside their Nix declarations. His superagent, worker
pairs, scheduler and local Gufo route are higher-level policy. Tarek's base
image does not inherit Tom's NAS master, provider keys, quotas or schedules.
That workflow can be added against Tarek's own accounts when its intended
behavior is chosen.

His hand-run DSH wrapper also has a long history of custom routing and policy
changes. A fresh owner should not unknowingly receive obsolete refusals or
assumptions merely by copying that wrapper. The image starts from the current
catalog's official DSH, its native provider/account setup and dshd; the shared
Imagine integration remains a separately versioned layer.

## Delivery and diagnostics

The fleet's useful operational lessons survive the move to one laptop:
build on designated compute, stage only source/non-secret inputs, preserve
the last working generation, inspect an activation plan, and distinguish
source publication from a running desktop. Runtime experiments need a private
runtime and compositor tests must never disrupt the user's D-Bus/session.
Keep unexpected failures and coredumps visible instead of repairing a test
by restarting the user's manager.

Tom's old source-only and engine-only upgrades are a reason to record actual
pins and qualification together. Tarek's release records the kernel, hardware
module source, Domicile/Imagine source and compiled closure. First-boot
onboarding separately checks the real Wi-Fi, quiet audio, camera, Touch Bar,
display, battery and fan behavior. This makes later shared-shell contributions
reviewable without pretending a VM proves this physical Mac's hardware.
