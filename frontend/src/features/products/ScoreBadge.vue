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

const sourceLabel = computed(() =>
  props.source === null ? "not scored" : props.source.startsWith("llm") ? "AI" : "formula",
);
</script>

<template>
  <div class="badge" :data-tone="tone" :title="`Scored by ${sourceLabel}`">
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <circle class="badge__track" cx="24" cy="24" r="20" />
      <circle class="badge__value" cx="24" cy="24" r="20" :stroke-dasharray="dash" />
    </svg>
    <span class="badge__score">{{ score ?? "—" }}</span>
    <span class="badge__source">{{ sourceLabel }}</span>
  </div>
</template>

<style scoped>
.badge {
  position: relative;
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  flex: none;
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
  position: absolute;
  bottom: -1.05rem;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}
</style>
