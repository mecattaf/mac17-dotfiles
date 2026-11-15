{ lib, stdenv, fetchFromGitHub, pkg-config, libusb1, makeWrapper
, bash, coreutils, gnused, gnugrep, findutils, gawk, kmod, systemd, python3, util-linux
}:

stdenv.mkDerivation {
  pname = "pomona";
  version = "0.11.1";
  src = fetchFromGitHub {
    owner = "MarcoDiGioia";
    repo = "Pomona";
    rev = "2ef95b5852b257a9eadb46ba01d3260ead0c84ab";
    hash = "sha256-DlNy+ESaYxYgDKbNZMuJt2jRzg7SRy+37m1TEMps1o8=";
  };

  nativeBuildInputs = [ pkg-config makeWrapper python3 ];
  buildInputs = [ libusb1 ];
  buildPhase = ''
    runHook preBuild
    make build
    runHook postBuild
  '';
  installPhase = ''
    runHook preInstall
    install -Dm755 bin/pomona "$out/libexec/pomona"
    install -Dm755 build/pomona-t1-boot "$out/lib/pomona/pomona-t1-boot"
    install -Dm755 libexec/pomona-touchbard "$out/lib/pomona/pomona-touchbard"
    install -Dm755 libexec/pomona-admin "$out/lib/pomona/pomona-admin"
    install -m644 lib/*.sh "$out/lib/pomona/"
    install -Dm644 LICENSE "$out/share/doc/pomona/LICENSE"
    cp -r docs "$out/share/doc/pomona/"
    install -m644 THIRD_PARTY_NOTICES.md LEGAL.md "$out/share/doc/pomona/"
    patchShebangs "$out/libexec" "$out/lib/pomona"

    # The NixOS module owns configuration, driver builds and service enablement.
    # Keep upstream's boot/stop and diagnostics; reject imperative package and
    # /etc mutation commands before they reach upstream's distro-specific code.
    mkdir -p "$out/bin"
    cat > "$out/bin/pomona" <<EOF
    #!${bash}/bin/bash
    case "\''${1-}:\''${2-}" in
      wifi:fix|wifi:undo|audio:fix|audio:undo|sleep:disable|sleep:enable|enable:|disable:)
        echo 'This Pomona installation is managed by NixOS. Change services.mac17Hardware in mac17-dotfiles and rebuild.' >&2
        exit 2
        ;;
    esac
    exec "$out/libexec/pomona" "\$@"
    EOF
    chmod +x "$out/bin/pomona"

    wrapProgram "$out/bin/pomona" \
      --set POMONA_LIB "$out/lib/pomona/pomona.sh" \
      --set POMONA_LIBEXEC "$out/lib/pomona" \
      --set POMONA_NIXOS 1 \
      --set POMONA_FIRMWARE_DIR /run/current-system/firmware/brcm \
      --prefix PATH : ${lib.makeBinPath [ bash coreutils gnused gnugrep findutils gawk kmod systemd python3 util-linux ]}
    wrapProgram "$out/lib/pomona/pomona-touchbard" \
      --prefix PATH : ${lib.makeBinPath [ python3 ]}
    runHook postInstall
  '';

  # Diagnostics must recognize a declaratively built module, without pretending
  # that DKMS has been installed. Upstream tests still exercise the original
  # branches when POMONA_NIXOS is unset.
  postPatch = ''
    substituteInPlace lib/audio.sh \
      --replace-fail 'AU_UPSTREAM_COMMIT=89b22ff90b86468b186706861dd18663562defa7' \
        'AU_UPSTREAM_COMMIT=1931615d723899f64b352e9e7ed2368c21c49728' \
      --replace-fail 'au_package_added() { [ -n "$(au_installed_sources)" ]; }' \
        'au_package_added() { if [ "''${POMONA_NIXOS:-}" = 1 ]; then modinfo -n "$AU_MODULE" 2>/dev/null | grep -q /updates/; else [ -n "$(au_installed_sources)" ]; fi; }' \
      --replace-fail 'au_module_built() { au_package_added && au_module_file >/dev/null; }' \
        'au_module_built() { if [ "''${POMONA_NIXOS:-}" = 1 ]; then au_package_added; else au_package_added && au_module_file >/dev/null; fi; }' \
      --replace-fail 'au_installed_sources() { ls -1d "$POMONA_SRC_DIR/$AU_PKG"-* 2>/dev/null; return 0; }' \
        'au_installed_sources() { if [ "''${POMONA_NIXOS:-}" = 1 ]; then modinfo -n "$AU_MODULE" 2>/dev/null | grep /updates/ || true; else ls -1d "$POMONA_SRC_DIR/$AU_PKG"-* 2>/dev/null; fi; return 0; }' \
      --replace-fail 'au_foreign() {' \
        'au_foreign() { [ "''${POMONA_NIXOS:-}" = 1 ] && return 1;' \
      --replace-fail 'au_missing_tools() {' \
        'au_missing_tools() { [ "''${POMONA_NIXOS:-}" = 1 ] && return 0;'
    substituteInPlace bin/pomona \
      --replace-fail 'DKMS package installed' 'Sound driver available in this generation' \
      --replace-fail 'DKMS package     ' 'Sound package    '
  '';

  meta = {
    description = "Apple T1 boot, fixed Touch Bar modes, camera and hardware diagnostics";
    homepage = "https://github.com/MarcoDiGioia/Pomona";
    license = lib.licenses.gpl3Plus;
    platforms = [ "x86_64-linux" ];
    mainProgram = "pomona";
  };
}
