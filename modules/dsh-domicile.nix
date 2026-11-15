{ config, inputs, lib, pkgs, ... }:
let
  cfg = config.programs.mac17Domicile;
  desktop = config.programs.mac17Desktop.checkedConfig;
  package = pkgs.callPackage ../pkgs/dsh-domicile.nix {
    domicile = config.programs.domicile.package;
    imagineSource = desktop.source or desktop;
    inherit (cfg) desktopId sdkSource;
    runtimeUid = config.users.users.${cfg.user}.uid;
  };
in
{
  options.programs.mac17Domicile = {
    enable = lib.mkEnableOption "the same-user read-only Imagine snapshot helper";
    user = lib.mkOption { type = lib.types.str; default = "tarek"; };
    desktopId = lib.mkOption { type = lib.types.str; default = "tarek-mac17"; };
    sdkSource = lib.mkOption {
      type = lib.types.str;
      default = inputs.domicile.rev or "8115d932b41be551ca7769fc2e89e323e5692c8c";
      description = "Exact Domicile SDK source paired with the shell and engine.";
    };
    package = lib.mkOption { type = lib.types.package; readOnly = true; default = package; };
  };
  config = lib.mkIf cfg.enable {
    assertions = [ {
      assertion = cfg.sdkSource == (inputs.domicile.rev or cfg.sdkSource);
      message = "dsh-domicile SDK identity must match the selected Domicile input.";
    } ];
    users.users.${cfg.user}.uid = lib.mkDefault 1000;
    environment.systemPackages = [ package ];
    # Wait for initial source links/identity before offering the first login.
    # Wants+After deliberately adds no stop coupling to later HM activation.
    systemd.services.greetd = lib.mkIf config.services.greetd.enable {
      wants = [ "home-manager-${cfg.user}.service" ];
      after = [ "home-manager-${cfg.user}.service" ];
    };
    home-manager.users.${cfg.user} = { ... }: {
      home.activation.stageImagineSnapshotConfig = {
        before = [ "linkGeneration" ];
        after = [ "writeBoundary" ];
        data = "run ${package.stage}";
      };
    };
  };
}
