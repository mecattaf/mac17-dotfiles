{ targetSystem ? null, targetSource ? null, usbImage ? null, usbOnly ? false, installerScript ? ../../modules/install-prepared.sh, storageModule ? ../../modules/storage-contract.nix }:
let
  nixpkgs = builtins.getFlake "github:NixOS/nixpkgs/d5cc6833999746cffdfe0598f7bc801a57b887a9";
  pkgs = import nixpkgs.outPath { system = "x86_64-linux"; config.allowUnfree = true; };
  lib = pkgs.lib;
  minimalTarget = nixpkgs.lib.nixosSystem {
    system = "x86_64-linux";
    modules = [ storageModule ({ pkgs, ... }: {
      boot.kernelPackages = pkgs.linuxPackages_latest;
      boot.initrd.availableKernelModules = [ "virtio_pci" "virtio_scsi" "sym53c8xx" "virtio_blk" "sd_mod" ];
      networking.hostName = "mac17-fixture-target";
      users.users.tarek.isNormalUser = true;
      system.stateVersion = "26.05";
    }) ];
  };
  preparedTarget = if targetSystem != null then builtins.storePath targetSystem else minimalTarget.config.system.build.toplevel;
  preparedSource = if targetSource != null then builtins.storePath targetSource else pkgs.runCommand "mac17-synthetic-source" {} ''
    mkdir -p "$out"
    echo '{"version":7,"nodes":{}}' > "$out/flake.lock"
    echo 'Synthetic test source. Never use as a real device configuration.' > "$out/README"
  '';
  guestPython = pkgs.python3.withPackages (ps: [ ps.pexpect ]);
in pkgs.testers.runNixOSTest {
  name = if usbOnly then "mac17-single-usb-mount" else "mac17-installer-disposable-disks";
  nodes.machine = { pkgs, lib, ... }: {
    boot.kernelPackages = pkgs.linuxPackages_latest;
    boot.initrd.availableKernelModules = [ "sym53c8xx" ];
    boot.loader.systemd-boot.enable = false;
    virtualisation = {
      useBootLoader = false;
      useEFIBoot = true;
      mountHostNixStore = true;
      memorySize = 4096;
      diskSize = 4096;
      vlans = [ ];
      qemu.networkingOptions = lib.mkForce [ ];
      qemu.diskInterface = "scsi";
      qemu.options = [ "-nic none" "-smbios type=1,manufacturer=QEMU,product=MacBookPro14,,3" ]
        ++ lib.optionals (usbImage != null) [
          "-device qemu-xhci,id=mac17usb"
          "-drive if=none,id=mac17usb,file=${builtins.storePath usbImage},format=raw,snapshot=on"
          "-device usb-storage,bus=mac17usb.0,drive=mac17usb,serial=MAC17-TEST-USB"
        ];
      emptyDiskImages = [
        {
          size = 65536;
          driveConfig.deviceExtraOpts = {
            product = "\"APPLE SSD VM\"";
            serial = "MAC17-TEST-TARGET";
          };
        }
        {
          size = 2048;
          driveConfig.deviceExtraOpts = {
            product = "\"MAC17 BACKUP\"";
            serial = "MAC17-TEST-BACKUP";
          };
        }
      ];
      additionalPaths = [ preparedTarget preparedSource ];
    };
    networking.useDHCP = false;
    nix.settings = {
      substituters = lib.mkForce [ ];
      builders = lib.mkForce "";
      experimental-features = [ "nix-command" "flakes" ];
    };
    environment.systemPackages = with pkgs; [
      coreutils cryptsetup dosfstools e2fsprogs findutils gawk gptfdisk gnugrep gnused
      gnutar gzip jq nixos-install nixos-enter openssh parted rsync util-linux
      systemd guestPython
    ];
    environment.etc."mac17-test/install-prepared.sh".source = installerScript;
    environment.etc."mac17-test/run-installer.py".source = ./run-installer.py;
    environment.etc."mac17-test/usb-proof-enabled".text = if usbImage != null then "yes" else "no";
    environment.etc."mac17-test/mount-usb-backup.sh".source = ./mount-usb-backup.sh;
    environment.etc."mac17-test/wrong-model".text = "SyntheticWrongModel\n";
    environment.etc."mac17-test/environment.json".text = builtins.toJSON {
      targetSystem = toString preparedTarget;
      targetSource = toString preparedSource;
      sourceRevision = "synthetic-qemu-install-proof";
    };
    environment.etc."mac17/install/image.json".text = builtins.toJSON {
      schema = 1;
      targetSystem = toString preparedTarget;
      sourceRevision = "synthetic-qemu-install-proof";
    };
  };
  testScript = builtins.readFile (if usbOnly then ./usb-test.py else ./test.py);
}
