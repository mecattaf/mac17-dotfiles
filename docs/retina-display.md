# First-session Retina configuration

Start the installed laptop with its lid open and external monitors disconnected.
The shell observes Domicile's public `displays.list` fields. Once the only
connected screen reports its native 2880×1800 mode, the host helper writes one
profile at scale 2, using the output name actually reported by this laptop. The
desktop then has a 1440×900 logical workspace. No EDID, connector name or serial
from another machine is shipped.

The host activation stages a real private
`~/.config/domicile/domicile.json`, rather than a Nix-store symlink. The native
Displays Settings page can therefore save later preferences. On upgrades a
three-way merge propagates untouched defaults while preserving user changes
and deletions in input, output and theme. The current generation always updates
the prebuilt shell path. Every candidate is checked by the selected Domicile
binary before an atomic replacement, and identical content is left untouched.
Private migration state lives under
`~/.local/state/mac17-display-config` (or `$XDG_STATE_HOME`).

Learning happens once. It defers if the desktop is locked, the physical mode is
unknown, a display is rotated, or more than one screen is connected. Existing
output profiles remain user-owned. A later scale change in Displays Settings
is preserved; the observer does not reset it to 2.

This first-run profile deliberately covers the laptop alone. Domicile profiles
must cover the exact connected display set. With a dock or external screen,
create and test a separate layout in Displays Settings; disconnecting that
screen should return to the saved Retina profile. Physical acceptance still
needs to check the actual panel's reported mode, the one initial configuration
reload, Chrome and Kitty scaling, locking, suspend/resume and dock hotplug.
These are not established by unit or bundle checks.

The implementation follows the pinned Domicile source at
[`8115d932`](https://github.com/cprussin/domicile/tree/8115d932b41be551ca7769fc2e89e323e5692c8c):

- [`DomicileDisplay`](https://github.com/cprussin/domicile/blob/8115d932b41be551ca7769fc2e89e323e5692c8c/packages/chrome-sdk/src/domicile-host.ts)
  distinguishes physical modes, logical sizes and the integer advertised scale.
- [Profile matching](https://github.com/cprussin/domicile/blob/8115d932b41be551ca7769fc2e89e323e5692c8c/packages/domicile-config/src/profile.rs)
  requires the exact connected display set and accepts actual output names.
- [Settings configuration](https://github.com/cprussin/domicile/blob/8115d932b41be551ca7769fc2e89e323e5692c8c/packages/app-settings/src/config-state.ts)
  requires a writable runtime config to save preferences.

The host observer is a small overlay on the pinned standalone Imagine source;
it reads display metadata and calls this fixed helper. It does not own windows
or alter Imagine's source repository. The read-only dsh snapshot protocol and
its identity/schema remain unchanged.
