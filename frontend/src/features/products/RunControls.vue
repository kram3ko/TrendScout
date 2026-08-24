<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";

import { formatDate } from "@/shared/format";
import { ApiError } from "@/shared/http";

import { fetchRuns, triggerRun } from "./api";
import { browserRunActive } from "./runState";
import type { Run, RunKind } from "./types";

const POLL_INTERVAL_MS = 5000;

const emit = defineEmits<{ finished: [] }>();

const runs = ref<Run[]>([]);
const error = ref("");
const pendingKind = ref<RunKind | null>(null);
let timer: number | undefined;

const active = computed(() => runs.value.find((run) => run.status === "running") ?? null);
const latest = computed(() => (kind: RunKind) => runs.value.find((run) => run.kind === kind));

async function refresh(): Promise<void> {
  try {
    runs.value = await fetchRuns();
    browserRunActive.value = runs.value.some((run) => run.status === "running");
    error.value = "";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "Could not load run history";
  }
}

async function start(kind: RunKind): Promise<void> {
  pendingKind.value = kind;
  browserRunActive.value = true;
  error.value = "";
  try {
    await triggerRun(kind);
    await refresh();
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "Could not start the run";
    await refresh();
  } finally {
    pendingKind.value = null;
  }
}

// Polling only runs while a job is in flight, so an idle dashboard is silent.
watch(active, (current, previous) => {
  if (current && timer === undefined) {
    timer = window.setInterval(refresh, POLL_INTERVAL_MS);
  }
  if (!current && timer !== undefined) {
    window.clearInterval(timer);
    timer = undefined;
    if (previous) emit("finished");
  }
});

onUnmounted(() => window.clearInterval(timer));
void refresh();

function describe(run: Run | undefined): string {
  if (!run) return "never run";
  if (run.status === "running") return "running now…";
  if (run.status === "success") {
    return `${run.items_collected} item(s) · ${formatDate(run.finished_at)}`;
  }
  return `${run.status}: ${run.detail ?? "no detail"}`;
}
</script>

<template>
  <section class="card runs">
    <div class="runs__action">
      <button
        class="button"
        type="button"
        :disabled="browserRunActive || pendingKind !== null"
        @click="start('trends')"
      >
        Collect trends
      </button>
      <p class="muted">Google Trends · {{ describe(latest('trends')) }}</p>
    </div>

    <p v-if="error" class="alert alert--error runs__error">{{ error }}</p>
  </section>
</template>

<style scoped>
.runs {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 2rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.runs__action {
  display: grid;
  gap: 0.3rem;
  justify-items: start;
}

.runs__action p {
  margin: 0;
  font-size: 0.78rem;
}

.runs__error {
  flex-basis: 100%;
}
</style>
