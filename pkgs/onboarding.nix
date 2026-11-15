{
  lib,
  writeShellApplication,
  python3,
  kitty,
  networkmanager,
  tailscale,
  gh,
  glib,
  wrangler,
  seahorse,
  nautilus,
  usbutils,
  claudeCode ? null,
  freeAiPackage ? null,
  dshdPackage,
  repository ? "mecattaf/mac17-dotfiles",
}:
writeShellApplication {
  name = "mac17-onboarding";
  runtimeInputs = [ kitty networkmanager tailscale gh wrangler seahorse nautilus usbutils dshdPackage glib ]
    ++ lib.optional (claudeCode != null) claudeCode
    ++ lib.optional (freeAiPackage != null) freeAiPackage;
  text = ''
    export MAC17_REPOSITORY=${lib.escapeShellArg repository}
    export MAC17_JOURNEY=${../onboarding/onboarding-journey.json}
    export MAC17_BROWSER=/run/current-system/sw/bin/mac17-browser
    export MAC17_KITTY=${kitty}/bin/kitty
    export MAC17_NMCLI=${networkmanager}/bin/nmcli
    export MAC17_TAILSCALE=${tailscale}/bin/tailscale
    export MAC17_GDBUS=${glib}/bin/gdbus
    export MAC17_GH=${gh}/bin/gh
    export MAC17_WRANGLER=${wrangler}/bin/wrangler
    export MAC17_SEAHORSE=${seahorse}/bin/seahorse
    export MAC17_NAUTILUS=${nautilus}/bin/nautilus
    export MAC17_LSUSB=${usbutils}/bin/lsusb
    export MAC17_CLAUDE=${if claudeCode == null then "/run/current-system/sw/bin/claude" else "${claudeCode}/bin/claude"}
    export MAC17_AI=${if freeAiPackage == null then "/run/current-system/sw/bin/mac17-ai" else "${freeAiPackage}/bin/mac17-ai"}
    export MAC17_DSHD=${dshdPackage}/bin/dshd
    export MAC17_SUDO=/run/wrappers/bin/sudo
    exec ${python3}/bin/python3 ${../scripts/mac17-onboarding.py} "$@"
  '';
}
