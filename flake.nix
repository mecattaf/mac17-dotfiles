{
  description = "Tarek's managed MacBookPro14,3 NixOS desktop and prepared USB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    domicile.url = "github:cprussin/domicile";
    imagine = {
      url = "github:agency-agency/imagine";
      inputs.domicile.follows = "domicile";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    # Preserve the catalog's own package universe and signed binary cache.
    llm-agents.url = "github:numtide/llm-agents.nix";
    dshd = {
      url = "github:mecattaf/dshd.nix";
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
            # The prepared target is ext4. The generic rescue ISO's ZFS module
            # does not support this latest stable kernel and is not required.
            boot.supportedFilesystems.zfs = lib.mkForce false;
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
        iso = target.pkgs.callPackage ./pkgs/usb-backup/usb-image.nix {
          baseIso = self.nixosConfigurations.installer.config.system.build.isoImage;
        };
        raw-iso = self.nixosConfigurations.installer.config.system.build.isoImage;
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
