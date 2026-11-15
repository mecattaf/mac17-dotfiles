{ config, inputs, lib, pkgs, ... }:
let
  cfg = config.programs.mac17FreeAI;
  agents = inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system};
  package = pkgs.callPackage ../pkgs/free-ai.nix {
    opencodePackage = agents.opencode;
    antigravityPackage = agents.antigravity-cli;
  };
in {
  options.programs.mac17FreeAI = {
    enable = lib.mkEnableOption "prepared native free AI clients";
    package = lib.mkOption { type = lib.types.package; readOnly = true; default = package; };
  };
  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ];
    environment.etc."mac17/free-ai.md".source = ../docs/free-ai.md;
    # Mutable OAuth/keyring/DSH credentials are created by Tarek at runtime.
    # No API keys, paid model defaults, subscription or reused account state.
  };
}
