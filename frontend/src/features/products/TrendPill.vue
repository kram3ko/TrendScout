<script setup lang="ts">
import { computed } from "vue";

import { formatDate } from "@/shared/format";

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
  <div class="trend">
    <span class="pill" :data-direction="direction" tabindex="0">
      <span class="pill__dot" />
      {{ label }}
      <template v-if="trend?.latest_value !== null && trend?.latest_value !== undefined">
        · {{ trend.latest_value }}/100
      </template>
      <span class="trend__tooltip" role="tooltip">{{ title }}</span>
    </span>
    <span v-if="trend" class="trend__detail">
      “{{ trend.keyword }}” · {{ trend.points_count }} points · {{ formatDate(trend.collected_at) }}
    </span>
  </div>
</template>

<style scoped>
.trend {
  position: relative;
  display: grid;
  justify-items: start;
  gap: 0.25rem;
}

.pill {
  position: relative;
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

.trend__tooltip {
  position: absolute;
  z-index: 10;
  bottom: calc(100% + 0.45rem);
  left: 0;
  width: max-content;
  max-width: min(20rem, 75vw);
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 0.45rem;
  background: var(--surface);
  box-shadow: 0 6px 18px rgb(15 23 42 / 14%);
  color: var(--text);
  font-size: 0.72rem;
  font-weight: 400;
  line-height: 1.35;
  opacity: 0;
  pointer-events: none;
  transform: translateY(0.2rem);
  transition: opacity 120ms ease, transform 120ms ease;
}

.pill:hover .trend__tooltip,
.pill:focus-visible .trend__tooltip {
  opacity: 1;
  transform: translateY(0);
}

.trend__detail {
  font-size: 0.72rem;
  color: var(--text-muted);
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
