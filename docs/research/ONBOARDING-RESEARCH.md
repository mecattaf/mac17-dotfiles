# Tarek onboarding in Imagine

Research and adaptation design, 15 November 2026. The target is Tarek’s own MacBookPro14,3, his own accounts and repository, managed by Tom. This work reads upstream source and the existing Imagine implementation. It supplies an original machine-readable journey and keybinding design; it does not claim a running onboarding screen or a tested MacBook installation.

The useful combination is Omarchy’s current Quickshell network/account controls and first-login lifecycle, Yafti’s configuration-driven journey, and GNOME Tour’s short lessons. Imagine should present those functions through its existing public Domicile components. Chrome profile sign-in is the first account step. Network connection precedes it only when the device is offline; a complete preloaded installation does not need an account to install its desktop.

## Source identities

| Source | Inspected identity | Material |
| --- | --- | --- |
| Omarchy stable | v4.5.0, `97e664bd971fa5a8691d89440d3738143499c438`, released 5 November 2026 | Already contains Quickshell; stable first-login sequence, network panel, agent sign-in lifecycle |
| Omarchy current default branch | `quattro`, `41c76fd4d69a65611ce8148a67284808c1eb0ba2` | Newer agent panel includes explicit CLI download progress and additional account behavior; distinguish these additions from stable |
| Yafti | `d8839254e82b84fbe3fa4c5de753b38dbf123c22` | Python/GTK/libadwaita configuration, conditional screens and completion persistence; repository is archived |
| GNOME Tour | `060089c587f0512791920a5a47e61d5bc6f0fbd5` | Rust/libadwaita carousel, next/back/skip and a short workspace/search tour |
| GNOME Initial Setup | `f100cd8b515c23422ffa58f7845b1dd329fe0cf8` | Separate provisioning application; network page uses NetworkManager |
| surface-dots | `8ff404bc6f3334054ee2f76dddc943cede52723b` | Exact donor in Tom’s firstboot notes; current installer is Rust/Tauri and installs a Quickshell configuration |

Omarchy research starts from the actual current repository, not an assumption from its earlier Walker/Gum desktop. Its current default and stable release both contain `shell/` QML. User direction to inspect its Quickshell source is correct.

## What Omarchy actually does

### Start setup inside the authenticated desktop

[`default/hypr/autostart.lua`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/default/hypr/autostart.lua) starts the shell and `omarchy-provision-first-run` when Hyprland starts. It updates the D-Bus/systemd activation environment before session services. Imagine already has its own session setup; transplant the lifecycle intent, not this Hyprland launcher or another compositor.

[`bin/omarchy-provision-first-run`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/bin/omarchy-provision-first-run) checks one user completion marker before doing any setup. It runs final user provisioning, enables user units individually, runs platform-specific user setup, applies appearance/input defaults and speaker tuning, waits for notification availability, then sends ordered welcome and Git notifications and schedules network-dependent invitations. Each foreground step records start/completion/failure to the first-run log. The overall marker is written only when those foreground steps succeeded, so failure causes retry at a subsequent login.

This is a first-login lifecycle with actionable notifications, not one large linear onboarding QML component. The QML panels supply the actual controls that the invitations open. The distinction matters: we can keep the lifecycle and make Imagine’s presentation a coherent, resumable journey.

[`bin/omarchy-done`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/bin/omarchy-done) supplies `check`, `mark`, and `ensure`; `ensure` uses exclusive creation to invite only once. A marker that an invitation was shown is not proof that an account or Wi-Fi connection was configured. Imagine needs distinct invited, running, skipped, confirmed and observed states.

### Invite only for missing work

The [`welcome hook`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/install/user/first-run/welcome.sh) opens the keybinding menu from an actionable notification. The [`Git hook`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/install/user/first-run/git.sh) checks name and email before offering Git setup. This is worth retaining: a preconfigured machine should not ask Tarek to repeat work that is already correct.

[`bin/omarchy-setup-git`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/bin/omarchy-setup-git) keeps commit identity separate from GitHub authentication, permits noninteractive name/email configuration and offers the CLI’s own login when needed. For Tarek, validate the GitHub CLI account as `tarekcmahmoud`; accepting a repository invite and setting commit identity remain separate facts.

### Wait for NetworkManager before declaring the machine offline

[`install/user/first-run/wifi.sh`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/install/user/first-run/wifi.sh) waits for NetworkManager to finish initial connection attempts. It then checks current connectivity and prompts for Wi-Fi if needed. Network-dependent agent/fingerprint invitations wait for a connection in a detached worker, keeping the rest of the desktop usable. It offers updates only when there is something to update, so the first boot of current media does not prompt the user into a no-op.

For Tarek, the first network requirement should be Chrome login, not downloading packages. The prepared system closure and board firmware belong in the image. If he connects in the live environment to permit remote setup, copy only the selected NetworkManager connection profile into the target with its correct root ownership and permissions; do not assume an ephemeral live profile survives reboot. If installation is completely offline, he enters the password in installed Imagine on first boot.

### Use the native networking backend and show recoverable failures

[`shell/plugins/panels/network/Panel.qml`](https://github.com/omacom/omarchy/blob/41c76fd4d69a65611ce8148a67284808c1eb0ba2/shell/plugins/panels/network/Panel.qml) uses Quickshell’s NetworkManager backend, including the selected network’s `connectWithPsk` operation. It retains inline password input across scan updates, records which SSID owns an in-flight action, distinguishes connection/forget/disconnection failures and handles an independently completed NetworkManager connection. Its enterprise helper sends the password over stdin, not process arguments. The panel treats captive portals, restricted connectivity, radio state and slow connection attempts as actual states.

[`Model.js`](https://github.com/omacom/omarchy/blob/41c76fd4d69a65611ce8148a67284808c1eb0ba2/shell/plugins/panels/network/Model.js) holds much of the nonvisual parsing and error selection. The transplantable behavior is the state model and recovery, not a second nmcli poller alongside Domicile’s networking service.

Imagine already imports `QuickSettings`, `PortalSignIn` and `useCaptivePortal` in `src/imagine/Desktop.tsx`, and its Finder includes a Quick settings action. Open or focus that existing network UI from onboarding. Keep passphrases in NetworkManager’s native secret/profile handling, never journey state, logs or a Nix expression.

### Let account login survive the browser taking focus

The agent panel’s account flow is especially useful. In stable, [`Panel.qml`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/shell/plugins/agents/Panel.qml) starts a bounded account helper with `--events`, displays status and a browser/device code, offers a paste field only when needed, supports re-opening the authorization page, and cancels the login subprocess when explicitly cancelled. Login continues when the browser takes focus and the panel closes; the result also arrives as a desktop notification. The current default adds separate get/sign-in phases with progress before authentication.

[`bin/omarchy-agent-account-add`](https://github.com/omacom/omarchy/blob/41c76fd4d69a65611ce8148a67284808c1eb0ba2/bin/omarchy-agent-account-add) delegates to the providers’ native CLIs, keeps account-specific mutable homes, confirms successful authentication, handles an interrupted final account registration, and uses a private browser window when adding an additional account so the already signed-in subscription is not silently reused. Credentials do not become QML properties in the shell.

For Imagine, use a small reviewed adapter for each installed CLI. It should expose coarse typed status to the UI and launch the official sign-in flow in Kitty or Chrome. Do not parse arbitrary CLI stdout as executable commands, put tokens into a widget, or reuse Omarchy’s lazy mise installation: the CLI binaries will already be in Nix’s system closure.

Omarchy’s [`AuthServiceStore.js`](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/shell/services/AuthServiceStore.js) deliberately avoids a globally shared QML module instance that would give third-party plugins access to authentication-bearing service objects. Imagine should similarly expose actions/status, not credential-bearing service handles.

## Chrome first

After a usable connection exists, open the actual installed Google Chrome with Tarek’s persistent normal profile. The first account card says to use Chrome’s profile button and sign in. Signing into a Google website and signing the browser profile in are different choices; Google documents the latter explicitly. He should see his bookmarks and saved information before proceeding. [Google’s sign-in instructions](https://support.google.com/chrome/answer/185277?co=GENIE.Platform%3DDesktop&hl=en).

Completion here should be a clear user acknowledgement, not cookie scraping, profile-database parsing or a requirement to install a privileged browser extension. The shell can verify that Chrome launched; it cannot honestly infer that his desired account has finished synchronization from that fact.

Provide a working Secret Service before this first Chrome launch. Chromium documents GNOME Libsecret and KWallet storage and notes that unavailable backends can fall back to its basic store. The image should not paper over a missing keyring with `--password-store=basic`. [Chromium Linux password storage](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux/password_storage.md).

Tom’s current Zenbook configuration imports `modules/keyring-autounlock.nix`; that mechanism seals the keyring password to TPM2 because greetd autologins. This exact mechanism does not transplant to a T1 Mac without a standard TPM2. Start with password-based desktop login and PAM/keyring unlocking, or make a deliberate one-time keyring-unlock step. Preserve the keyring and Chrome profile in mutable private state and encrypted backup. Rebuilding NixOS must not reset either.

## Journey for Tarek

`onboarding-journey.json` is original design data with stable step/action identifiers and dependency rules. It orders the first account action as Chrome. The intended path is:

1. Connect if offline. Preloaded applications remain available without internet.
2. Sign into Chrome’s profile and recover his browser environment.
3. Join his own Tailscale account, invite Tom using the agreed management arrangement, and verify a real remote connection.
4. Authorize GitHub CLI as `tarekcmahmoud`, accept the repository invite and set commit identity.
5. Sign into Claude with his own subscription, then start and resume a DSH session.
6. Connect his Cloudflare account and Wrangler when ready; this optional setup should not hold the usable desktop hostage.
7. Check the MacBook’s physical input, camera, quiet audio, Wi-Fi and Touch Bar, with sleep/wake tracked separately.
8. Learn Finder, workspace rail, Kitty, assistant resume and Touch Bar through short actions on his actual desktop.
9. Open the Imagine contribution workspace and preview a small shell change.

The first complete setup pass needs only the account/device steps. Lessons are available immediately and can be skipped/reopened. An optional account step records Later rather than claiming success. A successful invitation is not a verified remote login. A module loading is not a verified microphone or speaker.

Tailscale membership invitation and sharing one machine are different arrangements. The source UI should say which is being used. The owner/invitee identity and final SSH policy must come from the management configuration, not a guessed email address in the journey. Tarek can keep ownership of his tailnet and invite Tom; the prepared USB must contain neither a reusable enrollment token nor cloned node state.

## State and Imagine integration

Use `$XDG_STATE_HOME/imagine/onboarding/state.json` for versioned progress, atomic writes and coarse non-secret results. A step records its identifier, step revision, state, last attempt and result category. An account becoming signed out later changes its current status without erasing the fact that Tarek already learned the desktop.

Keep four concepts separate: observed current readiness, user confirmation, a completed lesson, and a running login process. A live adapter owns a lease so reopening onboarding cannot start duplicate authentications. If the shell refreshes, it can reconnect to status or offer to reopen the native CLI rather than kill an unrelated process. Retry belongs to the failed action; it must not rerun installation or reset every account.

The manifest supplies typed action IDs resolved by reviewed adapters, never shell text from a downloaded manifest. NetworkManager handles network secrets, tailscaled owns its node identity, Chrome owns its profile/keyring, and each CLI owns mutable authentication state. The Nix configuration owns software and default paths. Fixed API keys can use the encrypted secret delivery pattern; refreshable OAuth stores should remain writable and never become read-only Nix-store links.

The existing Imagine `Desktop` should render onboarding as an ordinary shell-owned panel and participate in its existing modal/lock focus rules. It already routes actions through `useAgencyWindows`, the actual `WindowAction` reducer and `stageActionsOf`. A lesson about workspaces should observe those existing actions and state, not build a second desktop model. Onboarding must yield to screen lock and must not present a hidden approval control while locked.

The `dsh-domicile` transport currently describes read-only desktop introspection. Adding an onboarding button must not turn that channel into a generic execution capability. Touch Bar controls, pointer buttons and keyboard chords should call the same reviewed Imagine actions. Device introspection and mutations keep their respective owners.

## No Vim defaults

`non-vim-keybindings.json` gives semantic binding recommendations, not an installed keymap. Use the Mac Command key as Meta, arrow-key focus/move, numbered workspaces, visible Finder/rail controls and local Kitty. Set the initial terminal editor to Nano and leave normal Chrome editing/tab shortcuts intact. Do not blindly spread all of `DEFAULT_KEYBINDINGS` into Tarek’s config and assume that removes inherited Vim motions.

Tom’s client config currently has global `Control+n` and `Control+Shift+n` Chrome launchers and Meta+j/k output navigation. The former steals standard application shortcuts; the latter teaches Vim motions. Neither is a useful Tarek default. The Zenbook Meta+Return launcher reaches Tom’s NAS; Tarek’s terminal should reach his own configured host, with a local recovery option that remains usable when the network is down.

Explain terminal copy/paste (Ctrl+Shift+C/V) and cancellation (Ctrl+C) as part of the first Kitty lesson. Do not globally remap Ctrl+C to copy. A graphical editor can be selected later without making Vim a prerequisite to commit or configure the machine.

## Touch Bar as part of the tour

Keep Esc and the function row available through the reliable baseline even if the programmable renderer is unavailable. When the hardware research qualifies a custom renderer, the strip can show context-sized actions: Open Chrome / Continue while the browser setup is active; a Wi-Fi connection status without any password; workspace numbers; quiet audio/brightness controls; launch or return to the assistant; Back/Next during lessons.

These are controls, not evidence of authorization. Do not expose OAuth codes, tokens, passwords or private prompt text on the strip. Do not add an all-purpose Accept button that can approve an unrelated background request. Lock state suppresses sensitive status and mutations. A touch on a workspace button routes through the same Imagine reducer as the workspace rail; there is no independent Touch Bar window manager.

The first useful custom mode for Tarek as a designer is a preview selector for a few known Touch Bar layouts. He can edit source/configuration, see the preview and restore the baseline. Keep that work isolated from Domicile engine upgrades and T1 firmware recovery. Package/default design and machine facts remain separate.

## Recovered local lineage

- [`firstboot-wizard.md`](/home/tom/mecattaf/notes/references/devlogs/1h26/pre-sync/firstboot-wizard.md) names Yafti, eqsh, `harness/docs/onboarding.md`, surface-dots and momo’s first-run marker. It explicitly praises a visual multistep configuration picker, progress and inline completion.
- [`INTEL.md`](/home/tom/mecattaf/notes/references/devlogs/1h26/pre-sync/INTEL.md:160) preserves the choice among GNOME’s first step, eqsh and Yafti.
- [`bluebuild-goals.md`](/home/tom/mecattaf/notes/references/archive/claude-code-cloud-CONSOLIDATION-bluebuild-goals.md:164) already lists first-boot Chrome, gh, Tailscale and Claude setup. Line 239 again names the GNOME/eqsh/Yafti alternatives. Those are historical proposed tasks, not completed implementations.
- Tom’s [Miracle settings issue #235](https://github.com/miracle-wm-org/miracle-wm/issues/235), created 5 September 2024, proposes Yafti’s Python/libadwaita approach for a theme-following settings UI. This is a primary authored source for the earlier idea, not just an assistant’s retrospective summary.

Yafti’s [`app.py`](https://github.com/ublue-os/yafti/blob/d8839254e82b84fbe3fa4c5de753b38dbf123c22/yafti/app.py) hashes the configuration and supports run-on-change/run-once behavior; its [`screen/window.py`](https://github.com/ublue-os/yafti/blob/d8839254e82b84fbe3fa4c5de753b38dbf123c22/yafti/screen/window.py) builds configured screens and advances through a carousel. Borrow those concepts rather than reviving an archived Python application just to host Imagine’s UI.

GNOME Tour’s [`window.ui`](https://github.com/GNOME/gnome-tour/blob/060089c587f0512791920a5a47e61d5bc6f0fbd5/data/resources/ui/window.ui) and [`paginator.rs`](https://github.com/GNOME/gnome-tour/blob/060089c587f0512791920a5a47e61d5bc6f0fbd5/src/widgets/paginator.rs) provide short overview/search/workspace/gesture pages with back/next/skip and keyboard navigation. GNOME Initial Setup is a separate program with actual language, keyboard, network, account and password provisioning pages. Do not copy GNOME-specific gesture claims unless the installed Domicile configuration implements them.

The current surface-dots [`installer_readme.md`](https://github.com/snes19xx/surface-dots/blob/8ff404bc6f3334054ee2f76dddc943cede52723b/.source_codes/installer_src/installer_readme.md) identifies its installer as Rust/Tauri. It preflights inputs, backs up changed components, rolls back on failure and selects a Quickshell configuration. The historical note’s admired UI was configuring Quickshell; the currently published installer is not itself a QML wizard. No installer binary was run.

## Verification performed and remaining acceptance

Inspected pinned upstream/local source and checked both supplied JSON files parse, step IDs are unique, dependencies exist and form a DAG, and Chrome is the first account step. No compositor, upstream install script, browser profile, OAuth login or root networking action was executed. No live desktop/session was changed.

The implementation acceptance should exercise: offline image reaches Imagine with installed applications; correct Wi-Fi password persists into the target and after reboot; wrong password and captive portal are recoverable; Chrome sign-in survives a login/reboot and a Nix rebuild with its keyring; each CLI is Tarek’s own account; Tailscale management survives reboot; interrupted login resumes or retries without duplicate processes; onboarding can reopen after completion; no Vim requirement; lock wins over onboarding and Touch Bar; hardware lessons report physical outcomes rather than inferring them.
