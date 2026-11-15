# Imagine read-only DSH capability

First-party Host plugin for exact DSH 0.2.1-rc.2. Registers only
`domicile_snapshot` and `domicile_workspace`; no client component, GenUI grant,
mutation, generic exec, provider login or implicit desktop selection.

Configuration is server-owned: `python` is an absolute reviewed interpreter;
`registryPath` is an absolute owner-controlled file in the established registry
format. Its desktop keys become the exact tool schema enum. Configuration is
snapshotted at registration, so changing the file does not silently redirect
existing tools. The fixed runner invokes the packaged reviewed Python query;
model arguments cannot set executables, paths, SSH addresses or command text.

Arguments are strict objects with `desktop`, optional `expected` containing
both `epoch` and `revision`, and mandatory `workspace` for the workspace tool.
Unknown fields, invalid identifiers and stale references fail closed. Host's
JSON Schema subset cannot express the complete recursive layout contract;
the existing Python validator checks every returned snapshot before the tool
produces its canonical strict `{desktop,code,resultJson}` output. `resultJson`
is null on failure and contains the validated snapshot/workspace JSON on
success. The model sees that JSON directly. This avoids weakening validation
to an unconstrained recursive Host output schema or maintaining a second tree
validator. Titles, URLs, contents and native frame counters are excluded.

Typed codes distinguish unavailable transport, malformed reply, unknown
workspace, stale revision, changed mount epoch, locked desktop and cancellation.
No SSH/native stderr or exception text is returned. Host tool pipeline policy
and original cancellation signals apply. Calls remain exclusive; timeout and
cancellation terminate only the owned query process group. A remote helper
already delivered over SSH may finish within its own bounded deadline; its
nonce cleanup retains the documented late atomic writer race.

Build `python3 tools/pack.py ABS_FRESH_OUTPUT` on compute; install only the
resulting copied archive. No editable installer links. A native Claude bridge
needs a separately reviewed exact allowance for these two names, tool
advertisement and owned call/result lifecycle. Mounting this plugin alone does
not grant native Claude access. No production registration is currently made.
