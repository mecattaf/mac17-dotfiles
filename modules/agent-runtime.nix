{ config, inputs, lib, pkgs, ... }:
let
  cfg = config.programs.mac17Agents;
  # Consume the catalog's own package set: following our nixpkgs or using its
  # shared-nixpkgs overlay changes paths and loses the catalog's substitutes.
  agents = inputs.llm-agents.packages.${pkgs.stdenv.hostPlatform.system};
in
{
  imports = [ inputs.dshd.nixosModules.default ];

  options.programs.mac17Agents.enable =
    lib.mkEnableOption "native DSH and Tom's maintained dshd utility";

  config = lib.mkIf cfg.enable {
    # The catalog already supplies DSH's NixOS-compatible Node launcher. pnpm
    # is needed by DSH's native plugin manager; no global npm install is used.
    environment.systemPackages = [ agents.dsh pkgs.pnpm ];

    dshd = {
      enable = true;
      defaultRelease = "stable";
      releases.stable = {
        # Same official DSH as the hand-run CLI, without Tom's fleet wrapper.
        # "stable" names this reviewed release, not an upstream release channel.
        dsh = agents.dsh;
        # Keep upstream permission semantics. In particular, "default" is not
        # a DSH permission mode. DSH's profile/UI/user choices stay effective.
        unsetEnvironment = [
          # A retained instance must not inherit its creator's CLI identity.
          "CLAUDECODE"
          "CLAUDE_CODE_ENTRYPOINT"
          "CLAUDE_CODE_CHILD_SESSION"
          "CLAUDE_CODE_SESSION_ID"
          "CLAUDE_CODE_SESSION_ATTENDED"
          "CLAUDE_CODE_MESSAGING_SOCKET"
          "CLAUDE_CODE_MESSAGING_TOKEN"
          "CLAUDE_CODE_EXECPATH"
          "CLAUDE_PID"
          "CLAUDE_EFFORT"
          "CLAUDE_ENVELOPE"
          "CODEX_THREAD_ID"
          "DSH_SESSION_ID"
          "DSH_SHELL"
          "DSH_PROFILE_DIR"
          "DSH_WEB_URL"

          # dshd captures its invoking shell's environment in a durable recipe.
          # Save provider keys through DSH's native Settings -> Models instead.
          # These are variable NAMES only; no credential value enters Nix.
          "ANTHROPIC_API_KEY"
          "ANTHROPIC_AUTH_TOKEN"
          "CLAUDE_CODE_OAUTH_TOKEN"
          "OPENAI_API_KEY"
          "OPENAI_ACCESS_TOKEN"
          "CHATGPT_ACCESS_TOKEN"
          "GEMINI_API_KEY"
          "GOOGLE_API_KEY"
          "GOOGLE_GENERATIVE_AI_API_KEY"
          "GOOGLE_CLOUD_API_KEY"
          "DEEPSEEK_API_KEY"
          "DEEPSEEK_ACCESS_TOKEN"
          "GROQ_API_KEY"
          "MISTRAL_API_KEY"
          "COHERE_API_KEY"
          "NVIDIA_API_KEY"
          "CEREBRAS_API_KEY"
          "HF_TOKEN"
          "HUGGING_FACE_HUB_TOKEN"
          "HUGGINGFACE_API_KEY"
          "OPENROUTER_API_KEY"
          "OPENCODE_API_KEY"
          "OPENCODE_ZEN_API_KEY"
          "OPENCODE_ZEN_FREE_API_KEY"
          "AI_GATEWAY_API_KEY"
          "VERCEL_OIDC_TOKEN"
          "CLOUDFLARE_API_TOKEN"
          "CLOUDFLARE_WORKERS_AI_TOKEN"
          "CF_API_TOKEN"
          "GH_TOKEN"
          "GITHUB_TOKEN"
          "GITHUB_ACCESS_TOKEN"
          "AWS_ACCESS_KEY_ID"
          "AWS_SECRET_ACCESS_KEY"
          "AWS_SESSION_TOKEN"
          "AZURE_OPENAI_API_KEY"
        ];
      };
    };

    # No profile, settings file, credential, instance or enablement is created
    # here. ~/.dsh and ~/.local/state/dshd stay writable, owned by Tarek.
    # dshd's native CLI opts individual instances into autostart when wanted.
  };
}
