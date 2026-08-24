import { ref } from "vue";

export type ThemeMode = "auto" | "light" | "dark";
type ResolvedTheme = Exclude<ThemeMode, "auto">;

const STORAGE_KEY = "trendscout.theme";
const DARK_SCHEME = "(prefers-color-scheme: dark)";
const modes: readonly ThemeMode[] = ["auto", "light", "dark"];
const mode = ref<ThemeMode>("auto");
const systemTheme = window.matchMedia(DARK_SCHEME);

function isThemeMode(value: string | null): value is ThemeMode {
  return value !== null && modes.some((candidate) => candidate === value);
}

function resolveTheme(): ResolvedTheme {
  if (mode.value !== "auto") return mode.value;
  return systemTheme.matches ? "dark" : "light";
}

function applyTheme(): void {
  const resolved = resolveTheme();
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
}

export function initializeTheme(): void {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (isThemeMode(saved)) mode.value = saved;
  applyTheme();
}

export function useTheme() {
  function setTheme(next: ThemeMode): void {
    mode.value = next;
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme();
  }

  function cycleTheme(): void {
    const index = modes.indexOf(mode.value);
    setTheme(modes[(index + 1) % modes.length] ?? "auto");
  }

  return { mode, cycleTheme };
}

systemTheme.addEventListener("change", () => {
  if (mode.value === "auto") applyTheme();
});
