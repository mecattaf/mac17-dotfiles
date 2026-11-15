{
  lib,
  stdenvNoCC,
  python3,
  makeWrapper,
  writeText,
  writeShellScript,
  coreutils,
  gnutar,
  gzip,
  domicile,
  imagineSource,
  sdkSource,
  desktopId ? "tarek-mac17",
  runtimeUid ? 1000,
}:
assert builtins.match "[a-f0-9]{40}" sdkSource != null;
assert builtins.match "[a-z][a-z0-9-]{0,63}" desktopId != null;
let
  identity = {
    inherit desktopId sdkSource;
    imagineSource = toString imagineSource;
    runtimeDirectory = "/run/user/${toString runtimeUid}";
    domicileBinary = "${domicile}/bin/domicile";
    replyRoot = ".local/state/dsh-domicile/replies";
  };
  clientConfig = writeText "dsh-domicile-client.json" (builtins.toJSON identity);
  stage = writeShellScript "stage-dsh-domicile-client" ''
    set -euo pipefail
    umask 077
    configDirectory="$HOME/.config/dsh-domicile"
    if [ -L "$configDirectory" ]; then
      echo 'dsh-domicile config directory must be a real private directory' >&2
      exit 1
    fi
    ${coreutils}/bin/mkdir -p "$configDirectory"
    ${coreutils}/bin/chmod 0700 "$configDirectory"
    staged=$(${coreutils}/bin/mktemp "$configDirectory/.client.json.XXXXXX")
    trap '${coreutils}/bin/rm -f -- "$staged"' EXIT
    ${coreutils}/bin/install -m 0600 ${clientConfig} "$staged"
    ${coreutils}/bin/mv -Tf -- "$staged" "$configDirectory/client.json"
    trap - EXIT
  '';
in
stdenvNoCC.mkDerivation {
  pname = "dsh-domicile-mac17";
  version = "0.1.0";
  src = ../vendor/dsh-domicile;
  nativeBuildInputs = [ makeWrapper python3 gnutar gzip ];
  dontBuild = true;
  installPhase = ''
    runHook preInstall
    mkdir -p "$out/lib/dsh-domicile" "$out/bin" "$out/share/dsh-domicile/plugin/package"
    cp client_helper.py protocol.py query.py "$out/lib/dsh-domicile/"
    cp ${../scripts/mac17-desktop-snapshot.py} "$out/lib/dsh-domicile/local_query.py"
    cp README.md SOURCE.json "$out/share/dsh-domicile/"
    cp -R plugin/lib plugin/package.json plugin/README.md "$out/share/dsh-domicile/plugin/package/"
    mkdir -p "$out/share/dsh-domicile/plugin/package/python"
    cp query.py protocol.py plugin/tool_runner.py "$out/share/dsh-domicile/plugin/package/python/"
    tar --sort=name --mtime=@1 --owner=0 --group=0 --numeric-owner \
      -cf - -C "$out/share/dsh-domicile/plugin" package | gzip -n > "$out/share/dsh-domicile/agency-dsh-domicile-0.1.0.tgz"
    makeWrapper ${python3}/bin/python3 "$out/bin/mac17-desktop-snapshot" \
      --add-flags "-I $out/lib/dsh-domicile/local_query.py" \
      --set DSH_DOMICILE_PAYLOAD "$out/lib/dsh-domicile" \
      --set DSH_DOMICILE_DESKTOP_ID ${lib.escapeShellArg desktopId} \
      --set DSH_DOMICILE_RUNTIME_UID ${lib.escapeShellArg (toString runtimeUid)} \
      --set DSH_DOMICILE_BINARY ${lib.escapeShellArg identity.domicileBinary} \
      --set DSH_DOMICILE_IMAGINE_SOURCE ${lib.escapeShellArg identity.imagineSource} \
      --set DSH_DOMICILE_SDK_SOURCE ${lib.escapeShellArg sdkSource}
    runHook postInstall
  '';
  passthru = { inherit clientConfig stage identity; };
  meta = {
    description = "Read-only local Imagine snapshots using the reviewed dsh-domicile protocol";
    platforms = lib.platforms.linux;
    mainProgram = "mac17-desktop-snapshot";
  };
}
