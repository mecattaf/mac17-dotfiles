{ lib, stdenvNoCC, python3, makeWrapper, domicile }:
stdenvNoCC.mkDerivation {
  pname = "mac17-display-config";
  version = "0.1.0";
  src = ../scripts/mac17-display-config.py;
  dontUnpack = true;
  dontBuild = true;
  nativeBuildInputs = [ makeWrapper ];
  installPhase = ''
    mkdir -p "$out/lib/mac17" "$out/bin"
    cp "$src" "$out/lib/mac17/display_config.py"
    makeWrapper ${python3}/bin/python3 "$out/bin/mac17-display-config" \
      --add-flags "-I $out/lib/mac17/display_config.py" \
      --set MAC17_DOMICILE_BINARY ${lib.escapeShellArg "${domicile}/bin/domicile"}
  '';
  meta = {
    description = "Writable Domicile preference merge and first Retina profile";
    platforms = lib.platforms.linux;
    mainProgram = "mac17-display-config";
  };
}
