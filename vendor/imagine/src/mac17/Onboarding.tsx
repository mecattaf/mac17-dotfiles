import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import type { Domicile } from "@domicile-desktop/sdk/desktop/desktop";
import type { AgencyBounds } from "../imagine/WorkspaceRail";
import { runHelperRequest } from "../imagine/HelperRequest";
import "./onboarding.css";

/** The host owns its manifest, account adapters and private progress store. */
export type OnboardingOptions = { helper: readonly string[] };
export type OnboardingHostAction = "network.open" | "tour.launcher" | "tour.workspaces";
type Progress = "pending" | "complete" | "deferred";
type Step = {
  id: string; title: string; body: string; action: string; required?: boolean;
  requires?: readonly string[]; status: Progress; running?: boolean;
  evidence?: "observed" | "acknowledged";
  completion?: { kind?: string; text?: string; acknowledgement?: string };
};
type SetupState = { schema: 1; visibility: "open" | "minimized" | "complete"; currentStep?: string; steps: Step[] };
type Probe = { state: string; message: string };
const hostActions = new Set<string>(["network.open", "tour.launcher", "tour.workspaces"]);
const initialStep = (state: SetupState) => state.steps.find(step => step.id === state.currentStep)
  ?? state.steps.find(step => step.status !== "complete" && step.status !== "deferred") ?? state.steps.at(-1);

function decode(value: unknown): SetupState {
  const data = value as SetupState;
  if (data?.schema !== 1 || !Array.isArray(data.steps) || data.steps.length > 40 ||
    data.steps.some(step => typeof step.id !== "string" || typeof step.title !== "string" ||
      typeof step.body !== "string" || typeof step.action !== "string" || !["pending", "complete", "deferred"].includes(step.status)))
    throw Error("Setup returned an unsupported response.");
  return data;
}

/** Opening is local intent. Refreshes, native logins and shell reloads never
 * pull focus back from a browser. Lock and other native panels take priority. */
export function useOnboarding({ domicile, config, blocked }: {
  domicile: Domicile; config?: OnboardingOptions; blocked: boolean;
}) {
  const [state, setState] = useState<SetupState>();
  const [requested, setRequested] = useState(false);
  const [locked, setLocked] = useState(domicile.session.locked !== false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [status, setStatus] = useState<Probe>();
  const alive = useRef(true), inFlight = useRef(false);
  const latest = useRef({ blocked, config, state }); latest.current = { blocked, config, state };
  const focusWanted = useRef(false), hydrated = useRef(false);
  const open = config !== undefined && requested && !blocked && !locked;
  const current = state === undefined ? undefined : initialStep(state);
  const canAct = () => !latest.current.blocked && domicile.session.locked === false;
  const call = useCallback(async (payload: unknown) => {
    const helper = latest.current.config?.helper;
    if (!helper?.length) throw Error("Setup is not configured on this computer.");
    const response = await runHelperRequest(domicile, helper, payload, 30000);
    if (response?.ok !== true) throw Error(typeof response?.error === "string" ? response.error : "Setup could not finish this action.");
    return response.result as unknown;
  }, [domicile]);
  const readProbe = useCallback(async (id: string) => {
    const result = await call({ op: "probe", step: id }) as Probe;
    if (typeof result?.state !== "string" || typeof result?.message !== "string") throw Error("Setup returned an unsupported status.");
    if (alive.current && latest.current.state && initialStep(latest.current.state)?.id === id) setStatus(result);
  }, [call]);
  const refresh = useCallback(async () => {
    if (!latest.current.config || domicile.session.locked !== false) return;
    try {
      const next = decode(await call({ op: "state" }));
      if (!alive.current) return;
      setState(next); latest.current.state = next; setError(undefined);
      if (!hydrated.current) {
        hydrated.current = true;
        setRequested(next.visibility === "open"); focusWanted.current = next.visibility === "open";
      }
      const selected = initialStep(next); if (selected) await readProbe(selected.id);
    } catch (cause) { if (alive.current) { setError(cause instanceof Error ? cause.message : "Setup is unavailable.");
      if (!hydrated.current) { hydrated.current = true; setRequested(true); focusWanted.current = true; } } }
  }, [call, domicile, readProbe]);
  useEffect(() => {
    alive.current = true;
    const stop = domicile.session.on("lockchange", () => {
      const isLocked = domicile.session.locked !== false; setLocked(isLocked);
      if (!isLocked) void refresh();
    });
    void refresh();
    return () => { alive.current = false; stop(); };
  }, [domicile, refresh]);
  useEffect(() => {
    if (open && focusWanted.current) { focusWanted.current = false; domicile.windows.focusShell(); }
  }, [open, domicile]);
  const minimize = () => {
    if (domicile.session.locked !== false) return;
    setRequested(false); focusWanted.current = false;
    void call({ op: "visibility", visibility: "minimized" }).catch(cause => { if (alive.current) setError(cause instanceof Error ? cause.message : "Progress could not be saved."); });
  };
  const command = (args: readonly string[]) => {
    if (args[0] !== "onboarding") return false;
    if (args.length !== 2 || !["open", "toggle"].includes(args[1] ?? "") || !config || !canAct()) return true;
    if (open && args[1] === "toggle") minimize();
    else {
      focusWanted.current = true; setRequested(true); void refresh();
      void call({ op: "visibility", visibility: "open" }).catch(() => {});
    }
    return true;
  };
  const operate = async (payload: unknown) => {
    if (!canAct() || inFlight.current) return;
    inFlight.current = true; setBusy(true); setError(undefined);
    try {
      const next = decode(await call(payload));
      if (alive.current) { setState(next); latest.current.state = next; setStatus(undefined); }
      return next;
    } catch (cause) { if (alive.current) setError(cause instanceof Error ? cause.message : "Setup could not save this step."); }
    finally { inFlight.current = false; if (alive.current) setBusy(false); }
  };
  const select = async (id: string) => {
    const next = await operate({ op: "select", step: id });
    if (next && canAct()) { try { await readProbe(id); } catch { if (alive.current) setStatus({ state: "unavailable", message: "Status could not be checked. Try again." }); } }
  };
  const complete = async (step: Step) => {
    const next = await operate({ op: "record", step: step.id, status: "complete" });
    if (!next || !canAct()) return;
    const at = next.steps.findIndex(s => s.id === step.id);
    const following = next.steps.slice(at + 1).find(s => s.status === "pending") ?? next.steps.at(-1);
    if (following) await select(following.id);
  };
  const defer = async (step: Step) => {
    const next = await operate({ op: "record", step: step.id, status: "deferred" });
    if (!next || !canAct()) return;
    const at = next.steps.findIndex(s => s.id === step.id);
    const following = next.steps.slice(at + 1).find(s => s.status === "pending") ?? next.steps.at(-1);
    if (following) await select(following.id);
  };
  const yieldAction = async (action: string, host?: (action: OnboardingHostAction) => void) => {
    if (!canAct() || inFlight.current) return;
    inFlight.current = true; setBusy(true); setError(undefined);
    try {
      await call({ op: "visibility", visibility: "minimized" });
      if (!canAct()) return;
      setRequested(false); focusWanted.current = false;
      await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      if (!canAct()) return;
      if (hostActions.has(action)) host?.(action as OnboardingHostAction);
      else await call({ op: "launch", action });
    } catch (cause) { if (alive.current) { setError(cause instanceof Error ? cause.message : "The native application could not open."); setRequested(true); } }
    finally { inFlight.current = false; if (alive.current) setBusy(false); }
  };
  const finish = async () => { const next = await operate({ op: "finish" }); if (next?.visibility === "complete") setRequested(false); };
  return { open, state, current, status, busy, error, command, minimize, refresh, select, complete, defer, yieldAction, finish,
    check: async () => { if (!current || !canAct()) return; try { await readProbe(current.id); } catch { setStatus({ state: "unavailable", message: "Status could not be checked. Try again." }); } } };
}

const actionLabel = (action: string) => ({
  "network.open": "Open Quick settings", "chrome.open-profile": "Open Chrome", "tailscale.login": "Sign in to Tailscale",
  "tailscale.open-users": "Open Tailscale Users", "github.login": "Sign in to GitHub", "claude.login": "Sign in to Claude",
  "dsh.first-session": "Open your assistant", "cloudflare.login": "Sign in to Cloudflare", "hardware.open-checks": "Open device checks",
  "tour.launcher": "Open Finder", "tour.workspaces": "Open the workspace rail", "tour.terminal": "Open Kitty",
  "tour.touchbar": "Open Kitty", "design.open-workspace": "Open your projects",
} as Record<string, string>)[action] ?? "Open this step";

export function Onboarding({ controller, bounds, onShellAction }: {
  controller: ReturnType<typeof useOnboarding>; bounds?: AgencyBounds;
  onShellAction: (action: OnboardingHostAction) => void;
}) {
  const panel = useRef<HTMLElement>(null), first = useRef<HTMLButtonElement>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const { current: step, state, status, open, busy, error } = controller;
  useEffect(() => { setAcknowledged(false); }, [step?.id]);
  useEffect(() => { if (open) first.current?.focus(); }, [open]);
  if (!open || bounds === undefined) return null;
  const completed = state?.steps.filter(s => s.status === "complete" && s.id !== "finish").length ?? 0;
  const dependencies = step?.requires?.filter(id => state?.steps.find(s => s.id === id)?.status !== "complete") ?? [];
  const manual = step?.completion?.kind !== "probe";
  const ready = manual ? acknowledged : status?.state === "ready";
  const finishing = step?.action === "onboarding.finish";
  const keyboard = (event: KeyboardEvent<HTMLElement>) => {
    if (event.nativeEvent.isComposing) return;
    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); controller.minimize(); }
    if (event.key === "Tab") {
      const nodes = Array.from(panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled),select:not(:disabled),input:not(:disabled),[tabindex="0"]') ?? []);
      const firstNode = nodes[0], last = nodes.at(-1);
      if (event.shiftKey && document.activeElement === firstNode) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); firstNode?.focus(); }
    }
  };
  return <div className="imagine-onboarding-layer" style={{ left: bounds.x, top: bounds.y, width: bounds.width, height: bounds.height }}>
    <section className="imagine-onboarding" ref={panel} role="dialog" aria-modal="true" aria-label="Set up your computer" onKeyDown={keyboard}>
      <header><h1>Set up your computer</h1><button ref={first} type="button" onClick={controller.minimize}>Minimize</button></header>
      {state && <label className="imagine-onboarding-step">Step
        <select value={step?.id ?? ""} disabled={busy} onChange={event => { void controller.select(event.currentTarget.value); }}>
          {state.steps.map(item => <option value={item.id} key={item.id}>{item.title}{item.status === "complete" ? " — done" : item.status === "deferred" ? " — later" : ""}</option>)}
        </select>
      </label>}
      {step && <main><h2>{step.title}</h2><p>{step.body}</p>
        {dependencies.length > 0 && <p role="status">First finish {dependencies.map(id => state?.steps.find(s => s.id === id)?.title ?? id).join(", ")}.</p>}
        {finishing ? <ul className="imagine-onboarding-review">{state?.steps.filter(s => s.id !== "finish").map(item =>
          <li key={item.id}><button type="button" disabled={busy} onClick={() => { void controller.select(item.id); }}>{item.title}</button><span>{item.status === "complete" ? item.evidence === "observed" ? "Checked" : "Confirmed" : item.status === "deferred" ? "Later" : "Unfinished"}</span></li>)}</ul>
          : <><div className="imagine-onboarding-actions"><button type="button" disabled={busy || step.running || dependencies.length > 0}
            onClick={() => { void controller.yieldAction(step.action, onShellAction); }}>{step.running ? "Already open in Kitty" : actionLabel(step.action)}</button>
            {step.completion?.kind === "probe" && <button type="button" disabled={busy} onClick={() => { void controller.check(); }}>Check again</button>}</div>
            {status && <p className="imagine-onboarding-status" role="status">{status.message}</p>}
            {manual && <label className="imagine-onboarding-confirm"><input type="checkbox" checked={acknowledged} disabled={busy || dependencies.length > 0}
              onChange={event => setAcknowledged(event.currentTarget.checked)} />{step.completion?.text ?? step.completion?.acknowledgement ?? "I tried this step and am ready to continue."}</label>}
            {step.id === "chrome" && <button className="imagine-onboarding-link" type="button" disabled={busy} onClick={() => { void controller.yieldAction("keyring.open"); }}>Open Passwords and Keys if Chrome needs its keyring</button>}</>}
      </main>}
      {error && <p className="imagine-onboarding-error" role="alert">{error}</p>}
      {!state && <button type="button" onClick={() => { void controller.refresh(); }}>Retry reading setup</button>}
      <footer><span>{completed} of {Math.max(0, (state?.steps.length ?? 1) - 1)} steps done</span><div>
        {step && !finishing && <button type="button" disabled={busy} onClick={() => { void controller.defer(step); }}>Later</button>}
        {step && (finishing ? <button type="button" disabled={busy} onClick={() => { void controller.finish(); }}>Finish setup</button>
          : <button type="button" disabled={busy || !ready || dependencies.length > 0} onClick={() => { void controller.complete(step); }}>Continue</button>)}
      </div></footer>
      <p className="imagine-onboarding-return">Setup stays available from Finder. Sign-in continues in Chrome or Kitty while this panel is minimized.</p>
    </section>
  </div>;
}
