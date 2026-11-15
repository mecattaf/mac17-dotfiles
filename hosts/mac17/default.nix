{ config, inputs, lib, pkgs, ... }:
{
  imports = [
    inputs.home-manager.nixosModules.home-manager
    inputs.domicile.nixosModules.default
    ../../modules/storage-contract.nix
    ../../modules/macbookpro14-3.nix
    ../../modules/base.nix
    ../../modules/agent-runtime.nix
    ../../modules/free-ai.nix
    ../../modules/desktop.nix
    ../../modules/dsh-domicile.nix
  ];
  networking.hostName = "tarek-mac17";
  boot.kernelPackages = pkgs.linuxPackages_latest;
  services.mac17Hardware.enable = true;
  programs.mac17Domicile.enable = true;
  programs.mac17Agents.enable = true;
  programs.mac17FreeAI.enable = true;
  system.configurationRevision = inputs.self.rev or inputs.self.dirtyRev or null;
  system.stateVersion = "26.05";
}
