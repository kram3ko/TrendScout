<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ score: number | null; source: string | null }>();

const CIRCUMFERENCE = 2 * Math.PI * 20;
const STRONG_SCORE = 70;
const MODERATE_SCORE = 45;

const tone = computed(() => {
  if (props.score === null) return "unknown";
  if (props.score >= STRONG_SCORE) return "strong";
  return props.score >= MODERATE_SCORE ? "moderate" : "weak";
});

const dash = computed(() => {
  const filled = ((props.score ?? 0) / 100) * CIRCUMFERENCE;
  return `${filled} ${CIRCUMFERENCE - filled}`;
});

const sourceKind = computed(() => {
  if (props.source === null) return "pending";
  return props.source.startsWith("llm") ? "ai" : "formula";
});

const sourceLabel = computed(() => {
  if (sourceKind.value === "ai") return "AI score";
  return sourceKind.value === "formula" ? "Formula" : "Pending";
});
</script>

<template>
  <div class="badge" :data-tone="tone" :data-source="sourceKind" :title="sourceLabel">
    <div class="badge__ring">
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <circle class="badge__track" cx="24" cy="24" r="20" />
        <circle class="badge__value" cx="24" cy="24" r="20" :stroke-dasharray="dash" />
      </svg>
      <span class="badge__score">{{ score ?? "—" }}</span>
    </div>
    <span class="badge__source">{{ sourceLabel }}</span>
  </div>
</template>

<style scoped>
.badge {
  display: grid;
  justify-items: center;
  gap: 0.35rem;
  width: 74px;
  flex: none;
}

.badge__ring {
  position: relative;
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
}

svg {
  position: absolute;
  inset: 0;
  transform: rotate(-90deg);
}

circle {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
}

.badge__track {
  stroke: var(--surface-muted);
}

.badge__value {
  stroke: var(--tone);
  transition: stroke-dasharray 0.3s ease;
}

.badge[data-tone="strong"] { --tone: var(--rising); }
.badge[data-tone="moderate"] { --tone: var(--flat); }
.badge[data-tone="weak"] { --tone: var(--falling); }
.badge[data-tone="unknown"] { --tone: var(--border); }

.badge__score {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1;
}

.badge__source {
  padding: 0.16rem 0.42rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-muted);
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  white-space: nowrap;
}

.badge[data-source="ai"] .badge__source {
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  background: color-mix(in srgb, var(--accent) 12%, var(--surface));
  color: var(--accent);
}
</style>
