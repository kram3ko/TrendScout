<script setup lang="ts">
import { computed } from "vue";

import { useTheme } from "./theme";

const theme = useTheme();

const labels = {
  auto: "Automatic theme",
  light: "Light theme",
  dark: "Dark theme",
} as const;

const icons = {
  auto: "◐",
  light: "☀",
  dark: "☾",
} as const;

const label = computed(() => labels[theme.mode.value]);
const icon = computed(() => icons[theme.mode.value]);
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="`${label}. Switch theme`"
    :title="`${label} · click to switch`"
    @click="theme.cycleTheme"
  >
    <span aria-hidden="true">{{ icon }}</span>
    <span>{{ theme.mode }}</span>
  </button>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 5.7rem;
  padding: 0.45rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: capitalize;
}

.theme-toggle:hover {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  color: var(--text);
}

.theme-toggle span:first-child {
  color: var(--accent);
  font-size: 1rem;
  line-height: 1;
}
</style>
