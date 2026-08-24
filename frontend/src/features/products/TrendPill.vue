<script setup lang="ts">
import { computed } from "vue";

import type { Trend } from "./types";

const props = defineProps<{ trend: Trend | null }>();

const LABELS: Record<string, string> = {
  rising: "Rising",
  flat: "Stable",
  falling: "Falling",
  unknown: "No data",
};

const direction = computed(() => props.trend?.direction ?? "unknown");
const label = computed(() => LABELS[direction.value] ?? LABELS.unknown);
const title = computed(() =>
  props.trend
    ? `“${props.trend.keyword}” — ${props.trend.points_count} points from Google Trends`
    : "No Google Trends reading yet",
);
</script>

<template>
  <span class="pill" :data-direction="direction" :title="title">
    <span class="pill__dot" />
    {{ label }}
  </span>
</template>

<style scoped>
.pill {
  display: inline-flex;
  /* The footer is a grid, so an inline element would otherwise stretch full width. */
  justify-self: start;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: var(--surface-muted);
  font-size: 0.78rem;
  font-weight: 550;
  color: var(--tone, var(--text-muted));
}

.pill__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentcolor;
}

.pill[data-direction="rising"] { --tone: var(--rising); }
.pill[data-direction="falling"] { --tone: var(--falling); }
.pill[data-direction="flat"] { --tone: var(--flat); }
</style>
