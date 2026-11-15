# Tarek's free AI setup

Reviewed 15 November 2026. This computer includes the official OpenCode 1.19.5
and Google Antigravity CLI 1.5.9 from the locked llm-agents catalogue. No Claude
subscription, API purchase, or Tom-owned account is required for the prepared
starting route. Accounts, quotas and credentials belong to Tarek.

## Start working

After Wi-Fi and Chrome profile sign-in, choose **Start a free AI assistant** in
Imagine setup, or open Kitty and run `mac17-ai setup`.

1. Choose Google Antigravity and sign in with your personal Google Account in
   Chrome. The free Individual plan includes native CLI use. No card is needed
   for this personal-account route. Ask a small question, wait for a real reply,
   then acknowledge the setup step. Installing the program or opening a login
   page does not count as a working account.
2. Later, type `agy` in a project directory. The launcher selects Gemini
   `gemini-3.8-flash-low`, disables AI-credit fallback, keeps one private account
   directory, and preserves the native permission prompts. `/usage` shows quota.
3. `zen` opens the official OpenCode terminal with public free models only.
   `zen "Explain this project"` sends a one-shot request; `zen -m
   glm-5.3-flash-free "Review this function"` explicitly selects the other
   prepared free model. Before launch, its native catalogue must report zero
   input/output/cache prices. There is no paid-model or provider fallback.

Antigravity's free quota refreshes weekly and depends on work done; it is not
the old Gemini CLI's advertised daily request allowance. Credit fallback is
disabled with `useG1Credits=false`. A limit means wait or explicitly choose a
different legitimate free service. [Plans](https://antigravity.google/docs/plans/),
[credit setting](https://antigravity.google/docs/cli/credits/),
[native personal-account sign-in](https://antigravity.google/docs/install/).

OpenCode's free models require its official client and are promotional: they
can disappear or have capacity limits. The pinned client contains a supported
anonymous/public free-model path. A fresh-home, credential-isolated check on
15 November reached the service but received **Free usage limit reached**;
anonymous availability is therefore not promised. It used no account key and
incurred no paid fallback. If this happens, use your Google account route.
[Current free models and privacy](https://opencode.ai/docs/console/models/),
[pinned official public fallback source](https://github.com/anomalyco/opencode/blob/v1.19.5/packages/opencode/src/provider/provider.ts).

## Add useful free API accounts in DSH

`mac17-ai providers` lists the fixed account destinations. For example,
`mac17-ai open groq` opens the official key page in Chrome. Signing up and
accepting terms happens in your browser. The computer never registers accounts,
adds payment methods, buys credits, or rotates accounts for you.

Use DSH's own **Settings → Models → Add model provider** flow. Choose the
catalogue's **Third-party model provider**, or its **Custom model API** form when
needed. Enter a key only in the native write-only credential field. DSH stores
credentials in its mutable `$DSH_HOME/.credentials.yaml` and references them
from profile configuration. Keep those files private and within encrypted
`/home`. A rebuild preserves them. Do not put keys in Git, the ISO, Nix options,
shell history, shell profiles, saved daemon environments, or chat messages.
Provider changes apply to subsequent requests without restarting the desktop.

Start with Google API and Groq. OpenRouter and Z.ai are useful additions.
Cloudflare is useful for deployed apps and bounded specialist models. Native
Antigravity/OpenCode access stays in its supported client; DSH does not bypass
OpenCode's client restriction or impersonate either vendor's client.

| Service | What is actually free now | Setup and boundary |
| --- | --- | --- |
| Google AI Studio / Gemini Developer API | Free input/output on eligible models, with project/model limits. Some projects require verification. | Own Google Account, API key from a project explicitly showing **Free**. Leave billing unlinked. Free-tier content can be used to improve Google products. [Billing](https://aistudio.google.com/docs/billing), [models/pricing](https://aistudio.google.com/docs/pricing). |
| Groq | Recurring Free organization tier; model-specific request/token limits. Limits apply to the organization, not each key. | Own account and key. Keep Free; adding a payment method to upgrade changes the charging model. A rate limit is not permission to rotate keys. [Limits](https://console.groq.com/docs/rate-limits), [billing](https://console.groq.com/docs/billing-faqs). |
| OpenRouter | Free variants: normally 20 requests/minute and 50/day for accounts without the credit-purchase threshold. Shared upstream pools can impose lower availability. | Own account/key, select exact `:free` variants or `openrouter/free`; keep provider price caps at zero and exclude paid fallbacks. Never use `auto` as a free guarantee. Purchases can raise the daily ceiling but are outside this setup. [Limits](https://openrouter.ai/docs/api_reference/limits), [source constants](https://github.com/OpenRouterTeam/docs/blob/main/snippets/exports/constants.mdx). |
| Cloudflare Workers AI | Workers Free includes 10,000 Neurons/day, resetting 00:00 UTC; operations stop at the allowance. | Own Cloudflare account plus a least-privilege Workers AI token for API use. Wrangler OAuth alone is not an inference token. Keep **Workers Free**; paid accounts charge overage. Several larger models require paid billing even before the allowance. [Current pricing and model exclusions](https://developers.cloudflare.com/workers-ai/platform/pricing/). |
| Z.ai | `glm-4.7-flash`, `glm-4.5-flash`, `glm-4.6v-flash` have free input/cache/output. Newer GLM5.x Flash and FlashX variants are paid. | Own API account/key. Check the account's current limits; no numeric public allowance is promised. Use exact free IDs. [Official pricing](https://docs.z.ai/guides/overview/pricing). |
| Mistral | Current Free mode includes monthly web Vibe/Studio usage. | Current admin docs explicitly exclude API access from Free mode and require billing/PAYG for API keys. Older official help still describes free API experiments; do not rely on it or enable billing to test. Browser free mode is useful. [Current usage/limits](https://docs.mistral.ai/admin/billing-usage/usage-limits). |
| Cohere | Evaluation keys: 1,000 API calls/month, with model/endpoint minute limits. | Own evaluation key. This is evaluation access, not a production budget. No production key or upgrade is provisioned. Useful for bounded text, embedding, or reranking experiments subject to terms. [Key types and limits](https://docs.cohere.com/docs/rate-limits). |
| NVIDIA API Catalog | Developer Program offers free hosted endpoints for prototyping; model/entitlement capacity varies. | Own Developer account/key and acceptance of trial/data terms. No fixed recurring allowance is established here; do not present old 1,000/5,000-credit figures as current entitlement. Not the first-run default. [Official developer FAQ](https://forums.developer.nvidia.com/t/nvidia-nim-faq/300317), [API documentation](https://docs.api.nvidia.com/nim/docs/introduction). |
| Cerebras | One-time $5 trial credit, expires after 30 days; **no renewing always-free API tier**. | Verified payment method required even for API/Playground activation. Access stops when the trial expires/exhausts unless you separately buy credits. Optional owner decision, not default onboarding. [Current limits and explicit trial FAQ](https://inference-docs.cerebras.ai/support/rate-limits). |
| Vercel AI Gateway | $5/month on eligible free-tier models, subject to verification and lower limits. | A valid payment method is needed to unlock credits. Buying credits ends the recurring free grant. Optional, left unprovisioned. Do not enable automatic top-up/BYOK fallback. [Pricing](https://vercel.com/docs/ai-gateway/pricing), [official setup prerequisite](https://vercel.com/academy/ai-summary-app-with-nextjs/ai-gateway-setup). |
| Hugging Face Inference Providers | Free users currently receive **no included API credits**. | Useful model/Spaces community account, but routed inference requires purchased credits or a paid subscription. It is not a prepared free API route. [Current pricing](https://huggingface.co/docs/inference-providers/pricing). |
| GitHub | Copilot Free remains available with a limited AI-credit allowance and automatic model choice; useful in supported native surfaces. | Own GitHub account; no Pro trial activated. GitHub Models' separate Playground/catalogue/API service was fully retired 30 July 2026. [Current Copilot plans](https://docs.github.com/en/copilot/get-started/plans), [Models retirement](https://docs.github.com/en/github-models). |

These are separate account allowances, not an unlimited combined pool. Quotas
change, some models are regional, and eligibility is verified in the provider's
own console. No paid service, subscription credit, anonymous quota, or trial is
counted as guaranteed free recurring capacity. Before sending design/client
material, check the chosen provider's current data-use terms. Google free API
and several promotional models may use content for improvement; keep private
material out unless you have approved that service's terms.

## Credentials and recovery

Antigravity uses the logged-in desktop's Secret Service where available; its
private native fallback/state root is
`~/.local/share/mac17-ai/antigravity`. Zen uses separate directories below
`$XDG_CONFIG_HOME/mac17-ai/zen`, `$XDG_DATA_HOME/mac17-ai/zen`, and corresponding
state/cache roots. Its public free route never reads a normal paid OpenCode
login. These roots are writable, owner-only, and excluded from the Nix image.
There are no numbered identities or account-rotation commands.

Back up DSH's mutable home and the desktop keyring only to your encrypted
personal backup. A reinstall cannot recreate OAuth tokens from dotfiles;
logging in again is the safe default. Do not restore Tom's CLI state. Secrets
never enter onboarding progress: that file records only acknowledged steps.

The `zen`/`agy` launchers are the prepared free entry points. Opening a provider's
normal website, installing another client, or explicitly enabling paid billing
does not inherit their safeguards. No background AI requests, quota farming,
automatic retry loop, account creation, or model rotation runs on this computer.
