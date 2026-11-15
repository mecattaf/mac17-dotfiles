{ config, inputs, lib, pkgs, ... }:
{
  imports = [
    inputs.home-manager.nixosModules.home-manager
    inputs.domicile.nixosModules.default
    inputs.dshd.nixosModules.default
    ../../modules/storage-contract.nix
    ../../modules/macbookpro14-3.nix
    ../../modules/base.nix
    ../../modules/desktop.nix
  ];
  networking.hostName = "tarek-mac17";
  boot.kernelPackages = pkgs.linuxPackages_latest;
  services.mac17Hardware.enable = true;
  system.configurationRevision = inputs.self.rev or inputs.self.dirtyRev or null;
  system.stateVersion = "26.05";
}
