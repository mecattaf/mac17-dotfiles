{ config, lib, pkgs, ... }:
let
  cfg = config.services.mac17Hardware;
  pomona = pkgs.callPackage ../pkgs/pomona.nix { };
  cs8409 = config.boot.kernelPackages.callPackage ../pkgs/cs8409.nix { };
  boardTemplate = pkgs.fetchurl {
    url = "https://gist.githubusercontent.com/madfatcat88/fb17a3ef6364a48a19ed57c143ddd383/raw/45b81e950597b0d53ba4cc6f79a35ea61e91aedf/brcmfmac43602-pcie.txt";
    hash = "sha256-+86fiYd1nurBLjbXJjfQgJRRV6lcZsKc6C28nKobGKE=";
  };
  # Keep a shared board template out of the per-device identity. The kernel
  # follows this link after mac17-wifi-board has generated a stable unique MAC.
  wifiFirmware = pkgs.runCommand "mac17-wifi-runtime-link" {
    # This is a runtime link, not a file the build host can compress.
    passthru.compressFirmware = false;
  } ''
    mkdir -p "$out/lib/firmware/brcm"
    ln -s /var/lib/mac17-firmware/brcmfmac43602-pcie.txt \
      "$out/lib/firmware/brcm/brcmfmac43602-pcie.txt"
  '';
in
{
  options.services.mac17Hardware = {
    enable = lib.mkEnableOption "MacBookPro14,3 hardware and Pomona";
    appleEsp = lib.mkOption {
      type = lib.types.str;
      default = "/boot/efi";
      description = "Mount point of this Mac's preserved Apple EFI partition.";
    };
    enableWifi = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Prepare the pinned BCM43602 board data before loading brcmfmac.";
    };
    enableAudio = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Build the Apple CS8409 sound driver with the selected kernel.";
    };
    allowSuspend = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable system suspend after physical sleep/wake qualification.";
    };
    touchbar = lib.mkOption {
      type = lib.types.submodule {
        freeformType = (pkgs.formats.json { }).type;
      };
      default = {
        default_mode = 2;
        fn_swaps = true;
        autodim = true;
        dim_timeout = 60;
        idle_timeout = 15;
        app_profiles = { };
      };
      description = "Pomona fixed-strip policy; app_profiles needs Imagine focus integration.";
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [
    {
      assertions = [
        {
          assertion = lib.versionAtLeast config.boot.kernelPackages.kernel.version "6.17";
          message = "mac17Hardware requires Linux 6.17 or newer; select the current stable kernel, with no release candidate.";
        }
      ];
      hardware.cpu.intel.updateMicrocode = lib.mkDefault true;
      hardware.enableRedistributableFirmware = true;
      boot.initrd.availableKernelModules = [ "applespi" "spi_pxa2xx_platform" "intel_lpss_pci" ];
      boot.initrd.kernelModules = [ "intel_lpss_pci" "spi_pxa2xx_platform" "applespi" ];
      boot.kernelModules = [ "applespi" "spi_pxa2xx_platform" "intel_lpss_pci" "uvcvideo" ];
      services.mbpfan.enable = true;
      services.upower.enable = true;
      hardware.sensor.iio.enable = true;
      environment.systemPackages = [ pomona pkgs.pciutils pkgs.usbutils pkgs.v4l-utils pkgs.alsa-utils pkgs.iw ];
      environment.etc."pomona/config.json".source = (pkgs.formats.json { }).generate "pomona-config.json" cfg.touchbar;
      services.udev.extraRules = ''
        ACTION=="add|change", SUBSYSTEM=="usb", ATTR{idVendor}=="05ac", ATTR{idProduct}=="8600", TEST=="power/control", ATTR{power/control}="on"
      '';
      systemd.services.pomona = {
        description = "Start Apple T1 from this Mac's preserved EFI firmware";
        wantedBy = [ "multi-user.target" ];
        after = [ "systemd-udevd.service" "local-fs.target" ];
        unitConfig.RequiresMountsFor = cfg.appleEsp;
        environment.POMONA_ESP = cfg.appleEsp;
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${pomona}/bin/pomona start";
          ExecStop = "${pomona}/bin/pomona stop";
          RemainAfterExit = true;
          TimeoutStopSec = 20;
        };
      };
      systemd.services.pomona-touchbard = {
        description = "Apple T1 fixed Touch Bar mode and Fn policy";
        wantedBy = [ "multi-user.target" ];
        after = [ "pomona.service" ];
        wants = [ "pomona.service" ];
        serviceConfig = {
          ExecStart = "${pomona}/lib/pomona/pomona-touchbard";
          Restart = "on-failure";
          RestartSec = 3;
        };
      };
    }
    (lib.mkIf cfg.enableAudio {
      boot.extraModulePackages = [ cs8409 ];
      boot.extraModprobeConfig = ''
        softdep snd_hda_intel pre: snd_hda_codec_cs8409
      '';
    })
    (lib.mkIf cfg.enableWifi {
      hardware.firmware = [ wifiFirmware ];
      boot.blacklistedKernelModules = [ "brcmfmac" ];
      boot.extraModprobeConfig = ''
        options brcmfmac feature_disable=0x82000
      '';
      networking.networkmanager.settings = {
        device."wifi.scan-rand-mac-address" = "no";
        connection."wifi.cloned-mac-address" = "permanent";
      };
      systemd.services.mac17-wifi-board = {
        description = "Prepare per-machine BCM43602 data before Wi-Fi starts";
        wantedBy = [ "multi-user.target" ];
        before = [ "NetworkManager.service" ];
        after = [ "local-fs.target" "systemd-machine-id-commit.service" ];
        path = [ pkgs.kmod ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          StateDirectory = "mac17-firmware";
          UMask = "0077";
        };
        script = ''
          ${pkgs.python3}/bin/python3 - <<'PY'
          import hashlib, os, pathlib, re
          machine = pathlib.Path('/etc/machine-id').read_bytes().strip()
          if not machine or machine == b'uninitialized':
              raise SystemExit('No stable machine identity; Wi-Fi board preparation stopped')
          digest = bytearray(hashlib.sha256(b'mac17-wifi:' + machine).digest()[:6])
          digest[0] = (digest[0] & 0xfc) | 0x02
          address = ':'.join(f'{part:02x}' for part in digest)
          board = pathlib.Path('${boardTemplate}').read_text()
          if len(re.findall(r'^macaddr=.*$', board, flags=re.M)) != 1:
              raise SystemExit('Unexpected Wi-Fi board template')
          board = re.sub(r'^macaddr=.*$', 'macaddr=' + address, board, flags=re.M)
          target = pathlib.Path('/var/lib/mac17-firmware/brcmfmac43602-pcie.txt')
          temporary = target.with_suffix('.tmp')
          temporary.write_text(board)
          os.chmod(temporary, 0o600)
          temporary.replace(target)
          PY
          modprobe brcmfmac
        '';
      };
    })
    (lib.mkIf (!cfg.allowSuspend) {
      # Locking and display blanking remain usable. Do not lose the first
      # unattended deployment to a known-unqualified T1/GPU suspend path.
      systemd.sleep.settings.Sleep = {
        AllowSuspend = false;
        AllowHibernation = false;
        AllowSuspendThenHibernate = false;
        AllowHybridSleep = false;
      };
      services.logind.settings.Login = {
        HandleLidSwitch = "lock";
        HandleLidSwitchExternalPower = "lock";
        HandleLidSwitchDocked = "ignore";
      };
    })
  ]);
}
