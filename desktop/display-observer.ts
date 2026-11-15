// Host-only read-only display observation. Imagine remains the window owner.
import type { Domicile } from "@domicile-desktop/sdk/desktop/desktop";
import { runHelperRequest } from "../imagine/HelperRequest";

/** Observe physical mode fields from the pinned SDK; scale is an advertised
 * integer and must not be multiplied by logical size to infer a mode. */
export function observeMac17Displays(domicile: Domicile): () => void {
  let disposed = false, running = false, last = "", pending = false;
  const inspect = () => {
    if (disposed || domicile.session.locked !== false || domicile.displays.list === undefined) return undefined;
    return { schema: 1, locked: false, displays: domicile.displays.list.map(display => ({
      name: display.name, modeWidth: display.modeWidth, modeHeight: display.modeHeight,
      width: display.width, height: display.height, scale: display.scale, transform: display.transform,
    })) };
  };
  const run = async () => {
    if (running) { pending = true; return; }
    const observation = inspect();
    if (observation === undefined) return;
    const signature = JSON.stringify(observation);
    if (signature === last) return;
    running = true;
    try {
      const result = await runHelperRequest(domicile,
        ["/run/current-system/sw/bin/mac17-display-config", "observe"], observation, 15000);
      if (result?.ok !== true) throw Error("Display configuration was not accepted");
      last = signature;
    } catch {
      // Bounded diagnostics only. The next display/unlock event may retry.
      if (!disposed) console.error("Mac display configuration is unavailable");
    } finally {
      running = false;
      if (pending && !disposed) { pending = false; void run(); }
    }
  };
  const stopDisplay = domicile.displays.on("change", () => { void run(); });
  const stopLock = domicile.session.on("lockchange", () => { void run(); });
  const dispose = () => { disposed = true; stopDisplay(); stopLock(); window.removeEventListener("pagehide", dispose); };
  window.addEventListener("pagehide", dispose, { once: true });
  void run();
  return dispose;
}
