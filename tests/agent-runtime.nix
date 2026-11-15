# Read-only evaluation of the actual host's lifetime and account-state boundary.
# nix eval --impure --json --expr 'import ./tests/agent-runtime.nix { flake = builtins.getFlake "path:/absolute/checkout"; }'
{ flake }:
let
  inherit (flake.inputs.nixpkgs) lib;
  config = flake.nixosConfigurations.mac17.config;
  agents = flake.inputs.llm-agents.packages.x86_64-linux;
  unit = config.systemd.user.units."dshd@.service".text;
  release = config.dshd.releases.stable;
  homeFiles = builtins.attrNames config.home-manager.users.tarek.home.file;
  ownedRuntime = lib.filter
    (path: path == ".dsh" || lib.hasPrefix ".dsh/" path
      || path == ".local/state/dshd" || lib.hasPrefix ".local/state/dshd/" path)
    homeFiles;
  instances = lib.filter
    (name: lib.hasPrefix "dshd@" name && name != "dshd@")
    (builtins.attrNames config.systemd.user.services);
  # Public launch defaults must not select an account or break DSH's schema.
  policy = release.environment.DSH_PERMISSION_MODE or "danger-full-access";
  failed = lib.filter (message: message != null) [
    (if config.programs.mac17Agents.enable then null else "agent runtime is disabled")
    (if release.dsh.outPath == agents.dsh.outPath
        && lib.any (package: package.outPath == agents.dsh.outPath) config.environment.systemPackages
      then null else "hand-run and retained DSH must use the same catalog package")
    (if lib.any (package: lib.getName package == "pnpm") config.environment.systemPackages
      then null else "DSH's native plugin manager needs pnpm")
    (if lib.elem policy [ "read-only" "workspace-write" "danger-full-access" ]
      then null else "the configured DSH permission mode is invalid")
    (if lib.hasInfix "X-RestartIfChanged=false" unit
        && lib.hasInfix "X-StopOnRemoval=false" unit
        && !lib.hasInfix "/nix/store/" unit
      then null else "updating the utility must preserve running instance bytes")
    (if instances == [ ] then null else "installation must not create or start agent instances")
    (if ownedRuntime == [ ] then null else "DSH account/profile and instance state must stay writable")
    (if lib.all (name: lib.elem name release.unsetEnvironment) [
      "CLAUDE_CODE_MESSAGING_TOKEN" "CODEX_THREAD_ID" "DSH_SESSION_ID"
      "ANTHROPIC_API_KEY" "OPENAI_API_KEY" "CLOUDFLARE_API_TOKEN" "GH_TOKEN"
    ] then null else "creator-session identities and exported tokens must not enter instance recipes")
  ];
in
assert lib.assertMsg (failed == [ ]) (lib.concatStringsSep "\n" failed);
{
  dsh = agents.dsh.name;
  dshd = config.dshd.package.name;
  inherit policy;
  excludedEnvironmentNames = builtins.length release.unsetEnvironment;
  nativePluginManager = true;
  mutableAccountState = true;
  noAutomaticInstances = true;
  runningInstancesSurviveSwitch = true;
}
