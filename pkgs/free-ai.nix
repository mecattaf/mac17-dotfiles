{ lib, writeShellApplication, symlinkJoin, makeDesktopItem, python3
, opencodePackage, antigravityPackage }:
let
  entry = name: route: writeShellApplication {
    inherit name;
    text = ''
      export MAC17_OPENCODE=${opencodePackage}/bin/opencode
      export MAC17_ANTIGRAVITY=${antigravityPackage}/bin/agy
      export MAC17_BROWSER=/run/current-system/sw/bin/mac17-browser
      exec ${python3}/bin/python3 ${../scripts/mac17-ai.py} ${route} "$@"
    '';
  };
  desktop = makeDesktopItem {
    name = "mac17-free-ai";
    desktopName = "Free AI assistants";
    comment = "Start a native free assistant or connect your own provider";
    exec = "kitty --class imagine-ai mac17-ai setup";
    icon = "utilities-terminal";
    categories = [ "Development" ];
  };
in symlinkJoin {
  name = "mac17-free-ai";
  paths = [ (entry "mac17-ai" "") (entry "zen" "zen") (entry "agy" "agy") desktop ];
  passthru = { inherit opencodePackage antigravityPackage; };
  meta = { description = "Single-owner native free AI clients with paid fallback disabled"; mainProgram = "mac17-ai"; license = lib.licenses.mit; };
}
