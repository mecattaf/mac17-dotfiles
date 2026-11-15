{ config, inputs, lib, pkgs, ... }:
let
  agents = inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system};
  managerKeys = lib.filter (s: s != "") (lib.splitString "\n" (builtins.readFile ../keys/managers.pub));
in {
  nixpkgs = {
    config.allowUnfree = true;
  };
  nix.settings = {
    experimental-features = [ "nix-command" "flakes" ];
    auto-optimise-store = true;
    substituters = [ "https://cache.nixos.org" "https://cache.numtide.com" ];
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypb1BB/c5LnjhQ9e7ON8FAzwG6E="
      "niks3.numtide.com-1:DTx8wZduET09hRmMtKdQDxNNthLQETkc/yaX7M4qK0g="
    ];
  };

  users.mutableUsers = true;
  users.users.tarek = {
    isNormalUser = true;
    description = "Tarek Mahmoud";
    linger = true;
    extraGroups = [ "wheel" "networkmanager" "domicile" ];
    shell = pkgs.fish;
    # The installer asks for his password locally. There is no factory login.
  };
  programs.fish.enable = true;
  programs.nano.enable = true;
  environment.variables = {
    EDITOR = "nano";
    VISUAL = "nano";
    BROWSER = "mac17-browser";
  };
  environment.systemPackages = with pkgs; [
    git gh curl jq ripgrep unzip nano networkmanager
    agents.claude-code wrangler
  ];

  networking.networkmanager.enable = true;
  networking.firewall.enable = true;
  services.tailscale = {
    enable = true;
    openFirewall = true;
    # No auth key or shared node identity. Tarek enrolls in his own account.
  };
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
  zramSwap = { enable = true; memoryPercent = 25; };
  services.power-profiles-daemon.enable = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    pulse.enable = true;
    wireplumber.enable = true;
  };
  security.rtkit.enable = true;
  security.polkit.enable = true;
  services.gnome.gnome-keyring.enable = true;
  security.pam.services.greetd.enableGnomeKeyring = true;
  xdg.portal.enable = true;
  hardware.graphics.enable = true;
  services.fstrim.enable = true;
  services.timesyncd.enable = true;
  services.automatic-timezoned.enable = true;
  i18n.defaultLocale = "en_US.UTF-8";
  console.keyMap = "us";
  console = { font = "ter-v24n"; packages = [ pkgs.terminus_font ]; };

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    backupFileExtension = "before-mac17";
    users.tarek = { ... }: {
      home.username = "tarek";
      home.homeDirectory = "/home/tarek";
      home.stateVersion = "26.05";
      programs.git = {
        enable = true;
        settings.user.name = "Tarek Mahmoud";
        settings.init.defaultBranch = "main";
      };
      programs.gh = {
        enable = true;
        gitCredentialHelper.enable = true;
      };
      # OAuth, Chrome, keyrings and ~/.dsh are deliberately writable.
      programs.fish = {
        enable = true;
        shellAliases = { ll = "ls -lah"; };
      };
    };
  };
}
