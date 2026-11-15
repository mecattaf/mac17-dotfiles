# A prepared installer using NixOS' maintained ISO and installation tools.
# The installed system is a separate, already-built closure.
{
  targetSystem,
  targetSource,
  sourceRevision ? "unqualified",
  managerKeys ? [ ],
  hardwareModule ? null,
}:
{
  lib,
  pkgs,
  modulesPath,
  ...
}:
let
  usbBackup = pkgs.callPackage ../pkgs/usb-backup/usb-backup.nix { };
  installer = pkgs.writeShellApplication {
    name = "mac17-install";
    runtimeInputs = with pkgs; [
      coreutils cryptsetup e2fsprogs findutils gawk gptfdisk gnugrep gnused
      gnutar gzip jq nixos-install nixos-enter openssh parted rsync util-linux
      systemd
    ] ++ [ usbBackup ];
    text = ''
      export MAC17_TARGET_SYSTEM=${lib.escapeShellArg (toString targetSystem)}
      export MAC17_TARGET_SOURCE=${lib.escapeShellArg (toString targetSource)}
      export MAC17_SOURCE_REVISION=${lib.escapeShellArg sourceRevision}
    '' + builtins.readFile ./install-prepared.sh;
  };
in
{
  imports = [ "${modulesPath}/installer/cd-dvd/installation-cd-minimal.nix" ]
    ++ lib.optional (hardwareModule != null) hardwareModule;

  networking.hostName = "mac17-installer";
  networking.networkmanager.enable = true;
  networking.wireless.enable = lib.mkForce false;

  # No login, password, device identity, Wi-Fi PSK or personalized EFI files
  # are placed in this derivation. Enrollment happens on the physical Mac.
  services.tailscale.enable = true;
  services.openssh = {
    enable = true;
    openFirewall = false;
    settings = {
      PasswordAuthentication = false;
      KbdInteractiveAuthentication = false;
      PermitRootLogin = "prohibit-password";
    };
  };
  users.users.root.openssh.authorizedKeys.keys = managerKeys;
  networking.firewall.interfaces.tailscale0.allowedTCPPorts = [ 22 ];

  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  environment.systemPackages = [ installer usbBackup pkgs.networkmanager pkgs.nixos-facter ];

  # storeContents takes full closures; includeSystemBuildDependencies is
  # intentionally not required when installing a prebuilt targetSystem.
  isoImage = {
    makeEfiBootable = true;
    makeUsbBootable = true;
    volumeID = "MAC17_INSTALL";
    storeContents = [ targetSystem targetSource ];
    squashfsCompression = "zstd -Xcompression-level 6";
  };
  environment.etc."mac17/install/image.json".text = builtins.toJSON {
    schema = 1;
    inherit sourceRevision;
    targetSystem = toString targetSystem;
    targetSource = toString targetSource;
    hardwareModel = "MacBookPro14,3";
    filesystem = "luks2-ext4";
    preservedPartition = "Apple EFI System Partition";
  };
  environment.etc."issue".text = ''
    Tarek's prepared NixOS installer

    The complete target system is on this USB. Installation can work offline.
    Run: sudo mac17-install --disk /dev/disk/by-id/<internal-Apple-SSD>
    This prints the plan only. Add --install after reviewing the plan and
    typing the on-device confirmation. Firmware backups go to this USB's
    writable backup partition; --backup-dir can select another mounted disk.

    Wi-Fi, if needed for remote assistance: nmtui
    The preferred account flow starts after installation: Wi-Fi, Chrome sign-in,
    Tailscale enrollment, then the remaining account connections.
  '';
}
