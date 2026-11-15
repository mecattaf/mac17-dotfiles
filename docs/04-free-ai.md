# 4. Start a free assistant

**Tarek completes any browser login. His AI explains the steps without handling
credentials.** Chrome and the network must already work. Claude Code is
optional; no Claude subscription is required for this phase.

1. In Imagine setup, choose **Start a free AI assistant**. Alternatively open
   Kitty with **Command ⌘ + Return** and run:

   ```sh
   mac17-ai setup
   ```

2. Choose **1 — Google Antigravity**. Sign in through Chrome using your own
   **personal Google Account**. The prepared launcher uses the free Individual
   route and disables paid-credit fallback. Do not add billing or buy credits.
3. Ask a small question, such as “Give me three ideas for a simple portfolio
   homepage.” Wait for an actual answer. Check `/usage` in the native client if
   you want to see quota. The free allowance depends on the work done and
   refreshes weekly; it is not unlimited.
4. Return to Imagine and acknowledge the step only after receiving the answer.
   Later, run `agy` from Kitty to return to this native assistant.

**Done:** your own account has returned a real reply without enabling paid
billing. Opening the client or its login page is not enough.

**If Google is unavailable:** `zen` opens official OpenCode with prepared free
models and no paid fallback. Public quota is not guaranteed: our isolated test
received a free-limit refusal. If it reports a limit, stop rather than buying
credits or trying multiple accounts. You can defer this onboarding step.

**Optional DSH setup:** open its session from Imagine setup. Choose **Settings →
Models → Add model provider**. Start with your own Google AI Studio Free-tier
project or Groq Free account. Enter the API key only in DSH's native write-only
credential field. Ask a small question and check for a reply before marking the
DSH step complete. A Google OAuth login in Antigravity does not create a DSH API
key. [Provider instructions and current free-tier limits](free-ai.md) explain
the other accounts; use that reference when adding one, not all at once.

**Stop if:** sign-in requires a paid plan, payment method or credit purchase;
the selected project is billed; a free quota is exhausted; or a key would need
to be pasted into chat/Git/a shell command. Keep account-creation and billing
decisions with Tarek. Never reuse Tom's tokens or rotate accounts to evade a
limit.

Next: [5. Check the Mac and contribute](05-verify-and-contribute.md).
