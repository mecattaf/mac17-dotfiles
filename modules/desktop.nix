{ config, inputs, lib, pkgs, ... }:
let
  domicile = config.programs.domicile.package;
  checkedConfig = pkgs.runCommand "mac17-imagine-config" { nativeBuildInputs = [ pkgs.jq ]; } ''
    set -euo pipefail
    export HOME="$TMPDIR"
    mkdir -p config
    printf '%s\n' '// Imagine source: ${../vendor/imagine}' > config/domicile.tsx
    cat ${../desktop/domicile.tsx} >> config/domicile.tsx
    cp -R ${../vendor/imagine} config/imagine
    chmod -R u+w config
    ${domicile}/libexec/domicile/builder --evaluate config/domicile.tsx --cache "$TMPDIR/cache" > evaluated.log
    cat evaluated.log
    evaluated=$(jq -rR 'fromjson? | select(.step == "evaluated") | .config' evaluated.log)
    test -n "$evaluated"
    ${domicile}/bin/domicile check-config "$evaluated"
    ${domicile}/libexec/domicile/builder --entry config/domicile.tsx --cache "$TMPDIR/cache"
    mkdir -p "$out"
    cp config/domicile.tsx "$out/"
    cp -R config/imagine "$out/imagine"
  '';
  chrome = pkgs.google-chrome.override {
    commandLineArgs = "--password-store=gnome-libsecret --ozone-platform=wayland";
  };
  browser = pkgs.writeShellApplication {
    name = "mac17-browser";
    runtimeInputs = [ pkgs.glib pkgs.coreutils ];
    text = ''
      # A browser login must not silently downgrade its credential storage.
      # Password-based PAM login starts and unlocks the login keyring.
      locked=$(timeout 10 gdbus call --session --dest org.freedesktop.secrets \
        --object-path /org/freedesktop/secrets/collection/login \
        --method org.freedesktop.DBus.Properties.Get org.freedesktop.Secret.Collection Locked)
      if [ "$locked" != '(<false>,)' ]; then
        echo 'Unlock the login keyring before opening Chrome.' >&2
        exit 1
      fi
      exec ${chrome}/bin/google-chrome-stable "$@"
    '';
  };
  session = pkgs.writeShellScriptBin "mac17-session" ''
    set -euo pipefail
    export BROWSER=mac17-browser
    export EDITOR=nano VISUAL=nano NIXOS_OZONE_WL=1
    export XDG_DATA_DIRS="${pkgs.glib.getSchemaDataDirPath pkgs.gsettings-desktop-schemas}:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
    ${pkgs.dbus}/bin/dbus-update-activation-environment --systemd \
      PATH HOME BROWSER EDITOR VISUAL NIXOS_OZONE_WL XDG_DATA_DIRS
    exec ${domicile}/bin/domicile --config "$HOME/.config/domicile/domicile.tsx"
  '';
in {
  options.programs.mac17Desktop.checkedConfig = lib.mkOption {
    type = lib.types.package;
    readOnly = true;
    default = checkedConfig;
    description = "The checked Imagine shell and Tarek's configuration.";
  };
  config = {
    programs.domicile = { enable = true; miracast = false; };
    environment.systemPackages = [ browser session chrome pkgs.libsecret ];
    services.dbus.packages = [ pkgs.nautilus ];
    services.greetd = {
      enable = true;
      settings.default_session = {
        command = "${pkgs.tuigreet}/bin/tuigreet --time --remember --cmd ${session}/bin/mac17-session";
        user = "greeter";
      };
    };
    # Changes must preserve an already running desktop and agent sessions.
    systemd.services.greetd.restartIfChanged = false;
    fonts.packages = [ pkgs.inter pkgs.jetbrains-mono ];

    home-manager.users.tarek = { ... }: {
      home.packages = [
        pkgs.kitty pkgs.nautilus pkgs.gnome-text-editor pkgs.seahorse
        pkgs.loupe pkgs.libnotify pkgs.pavucontrol
      ];
      home.sessionVariables = {
        BROWSER = "mac17-browser";
        NIXOS_OZONE_WL = "1";
      };
      programs.kitty = {
        enable = true;
        font = { name = "JetBrains Mono"; size = 12; };
        settings = {
          confirm_os_window_close = 1;
          enable_audio_bell = false;
          copy_on_select = false;
          background = "#000000";
          foreground = "#e6e6e6";
        };
      };
      xdg.configFile = {
        "domicile/domicile.tsx".source = "${checkedConfig}/domicile.tsx";
        "domicile/imagine".source = "${checkedConfig}/imagine";
      };
      xdg.mimeApps = {
        enable = true;
        defaultApplications = {
          "x-scheme-handler/http" = [ "mac17-chrome.desktop" ];
          "x-scheme-handler/https" = [ "mac17-chrome.desktop" ];
          "text/html" = [ "mac17-chrome.desktop" ];
          "application/pdf" = [ "mac17-chrome.desktop" ];
          "inode/directory" = [ "org.gnome.Nautilus.desktop" ];
          "text/plain" = [ "org.gnome.TextEditor.desktop" ];
          "text/markdown" = [ "org.gnome.TextEditor.desktop" ];
        };
      };
      xdg.desktopEntries.mac17-chrome = {
        name = "Google Chrome";
        exec = "mac17-browser %U";
        icon = "google-chrome";
        terminal = false;
        categories = [ "Network" "WebBrowser" ];
        mimeType = [ "x-scheme-handler/http" "x-scheme-handler/https" "text/html" ];
      };
    };
  };
}
