# DSH desktop introspection on Mac17

Mac17 runs its own agent host and desktop as Tarek. The installed
`mac17-desktop-snapshot` command reads Imagine's real reducer and final Stage
geometry through the existing dsh-domicile protocol. It does not SSH to Tom's
NAS or run a second desktop service.

```sh
mac17-desktop-snapshot --desktop tarek-mac17
mac17-desktop-snapshot --desktop tarek-mac17 --workspace 1
mac17-desktop-snapshot --desktop tarek-mac17 \
  --expect-epoch UUID --expect-revision 7
```

The explicit desktop ID is required. An unavailable, locked, ambiguous or
restarted desktop fails; the command does not return a cached previous result.
A workspace/container reference is scoped to its returned mount epoch and
semantic revision. A caller should obtain a fresh snapshot after a stale
reference rather than guess which window remains present.

## Installation and identity

Import `modules/dsh-domicile.nix` and set
`programs.mac17Domicile.enable = true`. The module defaults to user `tarek`,
UID1000 and desktop ID `tarek-mac17`; the SDK identity follows and must match the
selected Domicile input. It identifies the shared Imagine source through
`programs.mac17Desktop.checkedConfig.source`. These fields describe configured
provenance; they do not independently attest which engine is already loaded.

Home Manager stages `~/.config/dsh-domicile/client.json` atomically as an owned
mode0600 file in an owned mode0700 directory **before** `linkGeneration`. That
ordering matters because the existing Imagine hook reads identity once per
mount and retries after unlocking. The config is not a Nix-store symlink.
Identity-only changes need a shell remount coordinated with the checked bundle;
a helper must not relabel an older running shell as a new source.

The local wrapper requires the configured UID and an exact config match, checks
its source identities against each returned envelope, and calls the unchanged
reviewed `client_helper.request` directly. The helper owns private runtime/socket
and peer-UID checks, random nonce/reply directory, fixed native `send-shell`
operation, bounded deadline, no-follow reply opening and full schema/privacy
validation. It removes only its own nonce path. The documented late-writer
cleanup race remains visible; no broad runtime janitor has been added.

## What is available

- Actual outputs, scales, workspace membership and nested tiling/floating trees.
- Native/browser typed window identities, focus and final Stage placement geometry.
- Hidden scratchpad and managed background identities, with their existing semantics.
- Full snapshot and a single-workspace projection.
- Expected-epoch/revision rejection and failure while locked/unavailable.

Titles, URLs, document/page contents, environments and credentials are excluded
by the original schema validator. The response explicitly keeps mutation and
replayable-event capabilities false. No focus/layout action, generic command
execution, viewer termination or second window-manager model is added.

## DSH plugin status

The package also includes the existing first-party plugin as a copied archive:

```
share/dsh-domicile/agency-dsh-domicile-0.1.0.tgz
```

Its preserved source advertises exactly `domicile_snapshot` and
`domicile_workspace` and was documented/tested against DSH0.2.1-rc.2. Its Python
query route remains the original strict Tailscale SSH transport, with explicit
registry selection and no LAN fallback. It is included as reviewed lineage and
an activation artifact; it is **not silently registered in current DSH profiles**
and it does not become a local transport merely by being bundled.

The immediately supported single-laptop interface is the native command above,
which an agent can invoke using its ordinary command tool as Tarek. Registering
first-class names in a particular current DSH profile requires a reviewed
adapter using that version's public registry and the same local query contract.
It must not mutate every profile or install packages from npm at first boot.
Native Claude's tool advertisement is a separate integration; a DSH plugin
alone does not grant Claude a tool.

`vendor/dsh-domicile/SOURCE.json` records exact hashes and the production donor
commit. Client and protocol files match the production payload byte-for-byte.
No original working repository was edited. Nix parser and pure/static tests
cover packaging and guarded local dispatch; the actual socket/lock/reply flow
still needs isolated compositor validation against the selected source/engine
and then a real Mac17 acceptance query.
