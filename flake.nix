{
  description = "Tarek's managed MacBookPro14,3 NixOS desktop and prepared USB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/d5cc6833999746cffdfe0598f7bc801a57b887a9";
    home-manager = {
      url = "github:nix-community/home-manager/a1293da7dd8e497e08d26173f97e2976b36a31ea";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    domicile.url = "github:cprussin/domicile/8115d932b41be551ca7769fc2e89e323e5692c8c";
    # Preserve the catalog's own package universe and signed binary cache.
    llm-agents.url = "github:numtide/llm-agents.nix/aeb1afe1529c5dc7dcdc54d644a8aed212d99dd0";
    dshd = {
      url = "github:mecattaf/dshd.nix/e2df6ab724c7953e9a61b47588386675581b8359";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      makeSystem = modules: nixpkgs.lib.nixosSystem {
        inherit system modules;
        specialArgs = { inherit inputs; };
      };
      target = self.nixosConfigurations.mac17;
    in {
      nixosConfigurations = {
        mac17 = makeSystem [ ./hosts/mac17 ];
        installer = makeSystem [
          (import ./modules/offline-iso.nix {
            targetSystem = target.config.system.build.toplevel;
            targetSource = self;
            sourceRevision = self.rev or self.dirtyRev or "working-source";
            managerKeys = nixpkgs.lib.filter (s: s != "")
              (nixpkgs.lib.splitString "\n" (builtins.readFile ./keys/managers.pub));
            hardwareModule = ./modules/macbookpro14-3.nix;
          })
          ({ lib, pkgs, ... }: {
            boot.kernelPackages = pkgs.linuxPackages_latest;
            console = { font = "ter-v24n"; packages = [ pkgs.terminus_font ]; };
            services.mac17Hardware = {
              enable = true;
              # The installed system mounts its preserved ESP. In the live
              # image Pomona starts only after an explicit ESP mount.
              appleEsp = "/mnt/apple-efi";
            };
            systemd.services.pomona.unitConfig.ConditionPathExists =
              "/mnt/apple-efi/EFI/APPLE/EMBEDDEDOS/combined.memboot";
            systemd.services.pomona-touchbard.unitConfig.ConditionPathExists =
              "/mnt/apple-efi/EFI/APPLE/EMBEDDEDOS/combined.memboot";
            system.stateVersion = "26.05";
          })
        ];
      };
      packages.${system} = {
        iso = self.nixosConfigurations.installer.config.system.build.isoImage;
        system = target.config.system.build.toplevel;
        pomona = target.pkgs.callPackage ./pkgs/pomona.nix { };
        audio = target.config.boot.kernelPackages.callPackage ./pkgs/cs8409.nix { };
        touchbar-kernel = target.config.boot.kernelPackages.callPackage ./pkgs/react-drm-t1-kernel.nix { };
        desktop-config = target.config.programs.mac17Desktop.checkedConfig;
        default = self.packages.${system}.iso;
      };
      formatter.${system} = nixpkgs.legacyPackages.${system}.nixfmt;
    };
}
