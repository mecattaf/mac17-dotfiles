# dsh-domicile source payload

`client_helper.py` and `protocol.py` are exact copies of the reviewed production
payload in mecattaf/dotfiles commit435e61f084fce5f4892dad608703eb10a5ad8d49,
under `pkgs/client-desktop/dsh-domicile`.

`query.py` and `plugin/` preserve the existing staged first-party query/plugin
source, with exact file hashes in SOURCE.json. The original query remains a
strict inter-device Tailscale SSH transport. The preserved plugin documents
its DSH0.2.1-rc.2 compatibility and is packaged without automatic registration.

The host-owned same-user wrapper and identity staging are separate files in
this repository. See `docs/dsh-domicile.md` for supported local use, source
identity, privacy, lock behavior and activation limits.
