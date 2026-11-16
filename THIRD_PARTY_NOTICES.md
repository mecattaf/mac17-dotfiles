# License and provenance scope

The MIT license in [LICENSE](LICENSE) covers this repository's original Nix
configuration, integration code, scripts, tests and documentation. The
first-party `vendor/dsh-domicile` payload comes from Thomas Mecattaf's own
source; its exact origin and file hashes remain in
[vendor/dsh-domicile/SOURCE.json](vendor/dsh-domicile/SOURCE.json).

External software fetched by the flake or package definitions retains its
upstream copyright, license and notices. In particular, Pomona is declared
GPL-3.0-or-later, and the CS8409 and optional T1 DRM kernel drivers are declared
GPL-2.0-only in their package definitions. The packages preserve their upstream
source references and available notices; this repository's MIT license does
not replace those terms.

Imagine is fetched from its independent public repository and retains its
Manganese provenance. Nixpkgs, Domicile, Home Manager, llm-agents and dshd are
independent inputs with their own license terms. Chrome and firmware included
by a system configuration are separate software and are not relicensed by
making this configuration public.
