# DSH, dshd and updates

The USB includes native DSH, its Node runtime, pnpm for its plugin manager,
and Tom's separately maintained `dshd.nix` utility. These install without a
provider login. Tarek chooses his own provider during onboarding; a Claude
subscription and Tom's credentials are not prerequisites. The separate
[free AI setup](free-ai.md) covers the free services and their current limits.

## Package and state ownership

| Part | Source and owner | Update boundary |
| --- | --- | --- |
| `dsh` | `inputs.llm-agents.packages.x86_64-linux.dsh` | `llm-agents` lock input |
| `dshd` CLI and `dshd-run` | `github:mecattaf/dshd.nix`, through its native NixOS module | `dshd` lock input |
| Imagine + Domicile | shared public Imagine repository and its paired Domicile SDK/engine | reviewed `imagine` / `domicile` inputs |
| Models, credentials and conversations | Tarek's own DSH home, normally `~/.dsh` | native DSH settings and account refresh |
| Retained instance recipe and release roots | `~/.local/state/dshd/NAME` | native `dshd` commands |

At the initial source audit, the catalog pin was
`aeb1afe1529c5dc7dcdc54d644a8aed212d99dd0`, providing DSH **0.2.2-rc.3**;
the utility pin was `e2df6ab724c7953e9a61b47588386675581b8359`, current published
`main` on 2026-11-15. DSH is an upstream prerelease. The registry name `stable`
means the version reviewed in this system generation, not a different upstream
channel. The released image's `flake.lock` is the authority for its exact pins.

The audit compared the locked source with Tom's clean local utility checkout
at `a75495b29e1c003810f67899959922a81337a607`. The newer published source also
supports `dshd run --patch FILE -- ...` and `--stdin FILE` for headless tasks.
Those inputs are snapshotted into private instance state, so changing or
deleting the original file does not silently change a later run. This is
separate from DSH's live user-owned profiles. No utility source was copied
into this dotfiles repository.

This imports the current catalog's package set directly. It has
`overlays.shared-nixpkgs`, not the `overlays.default` mentioned in old comments
in Tom's dotfiles. Keep the catalog's own Nixpkgs pin and the configured signed
Numtide cache to reuse its prebuilt packages. Installing its entire catalog is
unnecessary; each installed client is selected explicitly.

There is no `npm install -g`, copied npm cache, frozen account directory or
declarative `~/.dsh` symlink. DSH itself initializes shipped `web`, `acp` and
`headless` profiles on first use. Its settings UI can then update its own
profiles and refresh accounts across NixOS rebuilds. pnpm is preinstalled for
optional native plugin operations. An optional Claude bridge is a separate
provider/plugin decision, not a mandatory replacement for native DSH.

## First use

From a project folder, run `dsh web` for an ordinary foreground session, or
use the retained form:

```sh
dshd run --name work -- web
dshd get work
dshd attach work
```

The web server can start without a model request. Follow its local address in
Chrome, choose a workspace, and open **Settings → Models → Add model provider**.
Use **Third-party model provider** for a provider in DSH's catalog, or **Custom
model API** for an endpoint outside it. The latter needs its provider ID, base
URL, supported API protocol and model IDs. Save Tarek's own key there; the UI
writes a secret to `$DSH_HOME/.credentials.yaml` and stores a credential
reference in the profile. Changes apply on the next request. The model picker
chooses the model and the default for future sessions. Do not infer free access
from a model's presence in the catalog; use the provider's actual free tier.

There is no automatic instance startup at install. Linger is enabled for Tarek
so he may opt a retained instance into boot startup later:

```sh
dshd enable work
dshd ls
dshd disable work
```

An SSH or browser disconnect does not cancel a retained session. ACP clients
use `dshd run --name editor -- acp`, then `dshd attach editor` as their agent
command. One controller owns an ACP session at a time; takeover is explicit.
Headless prompts execute once: use `dshd wait NAME` and `dshd read NAME` to
observe the same job. `dshd start --rerun NAME` deliberately submits it again.
Terminal and SDK profiles need their original frontend and are not supported
as retained dshd transports.

The native utility defaults retained instances to
`DSH_PERMISSION_MODE=danger-full-access`: they run as Tarek with normal native
file and process access. A profile setting, the UI's session choice, or a value
explicitly supplied at creation can select a different policy. The valid
spellings in the pinned DSH are `read-only`, `workspace-write`, and
`danger-full-access`; **`default` is invalid**. For an interactive retained
workspace with approval prompts, an explicit launch is:

```sh
env DSH_PERMISSION_MODE=workspace-write dshd run --name reviewed -- web
```

Keep that instance's UI/controller available to answer approvals. The module
does not introduce a policy wrapper or pin a provider, model or paid account.

## Credentials and backups

`dshd run` records its invoking shell's environment in a mode-0600 recipe.
The release strips Tom's creator-session identity names plus common provider,
GitHub, Cloudflare and cloud credential variables at creation and every start.
This prevents an unrelated CLI's exported token from becoming the instance's
durable configuration. Enter DSH API credentials through its native Models UI;
native client OAuth stays in that client's own writable account store. A new
provider may use another variable name: add that name to `unsetEnvironment` or
launch with `env -u VARIABLE` before creating the instance. This is an exact-name
list, not a general secret detector. A nonstandard environment-only adapter
needs an explicit runtime credential design before it is used with dshd.

Never put secret values in `dshd.releases.*.environment`: those values become
world-readable Nix store content and would enter the ISO. `DSH_HOME` may select
another writable DSH home; it is not scrubbed. Accounts, refresh tokens,
`~/.dsh`, `~/.claude*`, `~/.codex`, browser profiles and keyrings must stay out
of Git and the ISO. Preserve them only in Tarek's encrypted personal backup;
refresh or reauthorize normally when an upstream session expires. Chrome login
and CLI/provider login are separate account sessions.

`dshd get` reports environment names, not values. `dshd attach --print-url`
contains a login token, so do not put that output in issue reports or release
logs. The instance recipe is private runtime data, not a dotfile to commit.

## Keep Tom's utility current without moving the kernel

The input URLs name moving repositories while `flake.lock` records the reviewed
immutable commit. A URL ending in a hardcoded commit cannot advance with
`nix flake update`. Use:

```nix
llm-agents.url = "github:numtide/llm-agents.nix";
dshd = {
  url = "github:mecattaf/dshd.nix";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

Review Tom's upstream `dshd.nix` changes and tests, update only that input, then
inspect the lock diff:

```sh
nix flake update dshd
git diff -- flake.lock
jq '.nodes.dshd.locked | {rev, narHash, lastModified}' flake.lock
```

For a catalog/DSH update, use `nix flake update llm-agents` instead. These are
separate changes: neither requires moving the root Nixpkgs/kernel, Imagine or
Domicile. The catalog's own transitive package-set pins may move with it.
Do not add a `llm-agents.inputs.nixpkgs.follows` override: that discards the
cache-friendly package universe. Keep Imagine's source and its selected
Domicile SDK/engine coherent when updating those separately.

Build the candidate system on the designated NixOS compute host after checking
at least 25 GiB free on `/`. Inspect the activation plan, keep the previous
generation, and apply the reviewed system. On Tom's NAS, stage the non-secret
checkout on strix-coordinator and use `fleet-exec`; do not compile on NAS or
copy live account state to a builder. Push the reviewed source and lock update
to GitHub. No extra updater daemon, timer, copied utility source or fork is
needed; the same upstream utility supplies Tom and Tarek.

The current utility reports version `0.1.0` across more than one source
revision. Use the locked revision and actual store path, rather than
`dshd --version` alone, to identify an installed update:

```sh
readlink -f /run/current-system/sw/bin/dshd
dshd get work
```

A switch installs the new `dshd` CLI and release registry. It does **not**
replace the DSH or `dshd-run` bytes of a running instance. Each release pins
both, and per-instance `current` and `booted` garbage-collector roots preserve
them through switches, rollbacks and GC. Advance each instance deliberately:

```sh
dshd get work
dshd update work
# At the chosen interruption point, from another terminal:
dshd restart work
# Or combine selection and deliberate web/ACP restart:
dshd update -R work
```

`update` re-resolves the recorded registry name, reports closure changes and
selects the next release. It also removes newly excluded environment names
from the saved recipe. The running process keeps its current bytes/environment
until restart. An instance created from an absolute store path has no registry
name to follow, so `update` refuses it. Headless jobs are never resubmitted by
`update -R`; the new release is used at the next explicit `start --rerun`.

The static user-unit template sets `X-RestartIfChanged=false` and
`X-StopOnRemoval=false`. A NixOS switch must not restart the user manager to
make an update work. It does start the target: opted-in instances that were
stopped or failed may start again at a switch. Disable an instance if it
should stay stopped. Removing a stopped instance with `dshd rm NAME` releases
its roots while leaving DSH's own conversations and profiles intact.

## What carries over from Tom's setup

The source audit covered Tom's `modules/dshd.nix`, `home/dsh.nix`,
`home/agent-tools.nix`, `home/dsh-master.nix`, `pkgs/dsh/default.nix` and
`docs/dshd-nas.md`. His retained instances already use the official catalog
DSH, while his separate hand-run fleet wrapper routes agenix-provided keys,
selected plugins and fleet policy. This single-device implementation retains
the maintained native supervisor, explicit package selection, mutable account
state, signed catalog substitutes and separate update boundaries. Tarek's
provider setup and shell integration use his own identity. Tom's fleet roles,
account-slot rotations, private Gufo route and Master/scheduled worker profiles
are not prerequisites for using his laptop.

## Validation

`tests/agent-runtime.nix` evaluates the actual host configuration without
starting an instance. It checks the common DSH package, available pnpm,
valid permission mode, session-preserving static template, absence of
automatic instances, mutable DSH state and excluded creator/token variables.

`tests/test_dsh_boot.py` starts the actual pinned native CLI against a fresh
temporary DSH home and project folder with an allowlisted environment. On the
build host, run it through `~/.local/bin/runtime-test -- python3
tests/test_dsh_boot.py --dsh /nix/store/…-dsh-…/bin/dsh`. It verifies loopback
Web readiness, the launch-token/cookie authentication handshake, HTTP 200,
a writable native profile and clean shutdown, without a model request or
account login. Keep the target wrapper in the command even over SSH.

Both checks passed on 2026-11-15 against DSH 0.2.2-rc.3. The startup test ran
on strix-coordinator. It does not establish provider quota, a paid login,
ACP resume, or full dshd lifecycle behavior with a real model; upstream's
unit/contract/VM checks cover its supervisor contract separately.

Sources inspected at the pinned revisions:

- [DSH native provider setup](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.3/docs/user/guide/providers.md), also shipped in the installed CLI's `docs/user/guide/providers.md`.
- [Catalog DSH packaging](https://github.com/numtide/llm-agents.nix/blob/aeb1afe1529c5dc7dcdc54d644a8aed212d99dd0/packages/dsh/package.nix) and [cache/package-set contract](https://github.com/numtide/llm-agents.nix/blob/aeb1afe1529c5dc7dcdc54d644a8aed212d99dd0/README.md).
- [DSHd lifecycle and environment contract](https://github.com/mecattaf/dshd.nix/blob/e2df6ab724c7953e9a61b47588386675581b8359/README.md), [module options](https://github.com/mecattaf/dshd.nix/blob/e2df6ab724c7953e9a61b47588386675581b8359/nixos-modules/dshd/options.nix), and [update implementation](https://github.com/mecattaf/dshd.nix/blob/e2df6ab724c7953e9a61b47588386675581b8359/src/cli/update.rs).
