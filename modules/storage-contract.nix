# The prepared installer uses these stable labels, avoiding an install-time
# re-evaluation merely to substitute hardware UUIDs.
{ ... }:
{
  boot.initrd.luks.devices."mac17-root" = {
    device = "/dev/disk/by-label/MAC17_CRYPT";
  };
  fileSystems."/" = {
    device = "/dev/mapper/mac17-root";
    fsType = "ext4";
  };
  fileSystems."/boot" = {
    device = "/dev/disk/by-label/MAC17_BOOT";
    fsType = "ext4";
  };
  fileSystems."/boot/efi" = {
    device = "/dev/disk/by-partlabel/MAC17_EFI";
    fsType = "vfat";
    options = [ "umask=0077" ];
  };
  boot.loader = {
    systemd-boot.enable = false;
    efi = {
      efiSysMountPoint = "/boot/efi";
      canTouchEfiVariables = false;
    };
    grub = {
      enable = true;
      devices = [ "nodev" ];
      efiSupport = true;
      efiInstallAsRemovable = true;
      configurationLimit = 10;
    };
  };
}
