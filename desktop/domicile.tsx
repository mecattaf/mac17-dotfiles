// Tarek's device-independent Imagine entry; native output discovery remains on.
import type { ThemeConfig } from "@domicile-desktop/sdk/config";
import type { Shell as DomicileShell } from "@domicile-desktop/sdk/shell";
import { KeyAction } from "@domicile-desktop/sdk/key-action";
import { runImagine } from "./imagine/src/index";
import { observeMac17Displays } from "./imagine/src/mac17/display-observer";
import {
  DEFAULT_KEYBINDINGS, brightness, clipboard, exec, focus, fullscreen,
  launcher, lock, move, screenshot, volume,
} from "@domicile-desktop/manganese-window-management/keyboard/commands";
import { ownedChords } from "@domicile-desktop/sdk/own-keybindings";

// Keep the established gestures/workspace controls, with arrow-key navigation.
// Ordinary application Control shortcuts remain with Chrome and the editor.
const kept = Object.fromEntries(Object.entries(DEFAULT_KEYBINDINGS).filter(
  ([chord]) => !/^Meta\+(?:(?:Shift|Control)\+)*[hjkl]$/.test(chord)
));
const keybindings = {
  ...kept,
  "Meta+Return": exec("kitty"),
  "Meta+n": exec("mac17-browser"),
  "Meta+e": exec("nautilus"),
  "Meta+space": launcher(),
  "Meta+Left": focus("left"),
  "Meta+Right": focus("right"),
  "Meta+Up": focus("up"),
  "Meta+Down": focus("down"),
  "Meta+Shift+Left": move("left"),
  "Meta+Shift+Right": move("right"),
  "Meta+Shift+Up": move("up"),
  "Meta+Shift+Down": move("down"),
  "Meta+f": fullscreen(),
  "Meta+v": clipboard(),
  "Meta+Control+l": lock(),
  "Meta+Shift+o": KeyAction.SendShell(["imagine", "onboarding", "open"]),
  "Meta+Shift+s": screenshot(),
  XF86MonBrightnessDown: brightness("down"),
  XF86MonBrightnessUp: brightness("up"),
  XF86AudioMute: volume("mute"),
  XF86AudioLowerVolume: volume("down"),
  XF86AudioRaiseVolume: volume("up"),
};
ownedChords({ keybindings });

const imagineShell = runImagine({
  webBrowser: { command: ["mac17-browser"] },
  layoutPersistence: { identity: "tarek-mac17-layout-v1" },
  onboarding: { helper: ["/run/current-system/sw/bin/mac17-onboarding"] },
  keybindings: { keybindings },
});
export const Shell: DomicileShell = (root, domicile) => {
  observeMac17Displays(domicile);
  imagineShell(root, domicile);
};
export const shell_options = { font: "Inter", nightLight: { schedule: "off" } };
export const theme: ThemeConfig = {
  mode: "dark", accent_color: "#555451", cursor_size: 24,
  font_name: "Inter 11", monospace_font_name: "JetBrains Mono 11",
};
export const terminal = ["kitty"];
export const input = {
  touchpad: { natural_scroll: true, tap: true, disable_while_typing: "libinput" },
  keyboard: { repeat: { delay_ms: 500, rate: 25 } },
};
