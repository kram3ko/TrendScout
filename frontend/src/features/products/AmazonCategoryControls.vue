<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";

import { formatDate } from "@/shared/format";
import { ApiError } from "@/shared/http";

import {
  fetchAmazonCategories,
  fetchRuns,
  saveAmazonCategories,
  triggerRun,
} from "./api";
import type { AmazonCategory, Run, RunKind } from "./types";
import { browserRunActive } from "./runState";

const POLL_INTERVAL_MS = 2500;
const RUN_CLOCK_TOLERANCE_MS = 5000;

const emit = defineEmits<{ finished: [] }>();

const categories = ref<AmazonCategory[]>([]);
const selected = ref<string[]>([]);
const loading = ref(true);
const saving = ref(false);
const pendingKind = ref<RunKind | null>(null);
const error = ref("");
const latestRuns = ref<Run[]>([]);
let timer: number | undefined;
let runStartedAfter = 0;

const persisted = computed(() =>
  categories.value
    .filter((category) => category.enabled)
    .map((category) => category.slug)
    .sort(),
);
const normalizedSelection = computed(() => [...selected.value].sort());
const dirty = computed(
  () => JSON.stringify(persisted.value) !== JSON.stringify(normalizedSelection.value),
);
const latest = computed(
  () => (kind: RunKind) => latestRuns.value.find((run) => run.kind === kind),
);

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback;
}

async function loadCategories(): Promise<void> {
  loading.value = true;
  try {
    categories.value = await fetchAmazonCategories();
    selected.value = categories.value
      .filter((category) => category.enabled)
      .map((category) => category.slug);
  } catch (caught) {
    error.value = message(caught, "Could not load Amazon categories");
  } finally {
    loading.value = false;
  }
}

async function loadRuns(): Promise<void> {
  try {
    latestRuns.value = await fetchRuns();
    browserRunActive.value = latestRuns.value.some((run) => run.status === "running");
  } catch (caught) {
    error.value = message(caught, "Could not load run history");
  }
}

async function save(): Promise<boolean> {
  saving.value = true;
  error.value = "";
  try {
    categories.value = await saveAmazonCategories(selected.value);
    return true;
  } catch (caught) {
    error.value = message(caught, "Could not save category selection");
    return false;
  } finally {
    saving.value = false;
  }
}

async function start(kind: RunKind): Promise<void> {
  error.value = "";
  pendingKind.value = kind;
  browserRunActive.value = true;
  runStartedAfter = Date.now() - RUN_CLOCK_TOLERANCE_MS;
  try {
    if (kind === "amazon" && dirty.value && !(await save())) {
      pendingKind.value = null;
      browserRunActive.value = false;
      return;
    }
    await triggerRun(kind);
    beginPolling();
  } catch (caught) {
    error.value = message(caught, "Could not start the run");
    pendingKind.value = null;
    await loadRuns();
  }
}

function beginPolling(): void {
  window.clearInterval(timer);
  timer = window.setInterval(() => void poll(), POLL_INTERVAL_MS);
  void poll();
}

async function poll(): Promise<void> {
  await loadRuns();
  const kind = pendingKind.value;
  if (kind === null) return;
  const run = latestRuns.value.find(
    (item) => item.kind === kind && Date.parse(item.started_at) >= runStartedAfter,
  );
  if (!run || run.status === "running") return;

  window.clearInterval(timer);
  timer = undefined;
  pendingKind.value = null;
  browserRunActive.value = false;
  if (kind === "categories" && run.status === "success") await loadCategories();
  if (kind === "amazon" && run.status === "success") emit("finished");
}

function describe(run: Run | undefined): string {
  if (!run) return "never run";
  if (run.status === "running") return "running now…";
  if (run.status === "success") {
    return `${run.items_collected} item(s) · ${formatDate(run.finished_at)}`;
  }
  return `${run.status}: ${run.detail ?? "no detail"}`;
}

function selectAll(): void {
  selected.value = categories.value.map((category) => category.slug);
}

onUnmounted(() => window.clearInterval(timer));
void Promise.all([loadCategories(), loadRuns()]);
</script>

<template>
  <section class="card amazon-settings">
    <header class="amazon-settings__header">
      <div>
        <h2>Amazon collection</h2>
        <p class="muted">Choose the Best Sellers departments used by manual and scheduled runs.</p>
      </div>
      <button
        class="button button--ghost"
        type="button"
        :disabled="browserRunActive || pendingKind !== null || saving"
        @click="start('categories')"
      >
        {{ categories.length ? "Refresh categories" : "Discover categories" }}
      </button>
    </header>

    <p v-if="loading" class="muted amazon-settings__state">Loading categories…</p>
    <div v-else-if="categories.length" class="category-list">
      <label v-for="category in categories" :key="category.slug" class="category-option">
        <input v-model="selected" type="checkbox" :value="category.slug" />
        <span>{{ category.name }}</span>
      </label>
    </div>
    <p v-else class="amazon-settings__state muted">
      Discover the current department list directly from Amazon, then select what to collect.
    </p>

    <footer class="amazon-settings__footer">
      <div class="selection-actions">
        <button
          class="text-button"
          type="button"
          :disabled="!categories.length || browserRunActive || pendingKind !== null"
          @click="selectAll"
        >
          Select all
        </button>
        <button
          class="text-button"
          type="button"
          :disabled="!selected.length || browserRunActive || pendingKind !== null"
          @click="selected = []"
        >
          Clear
        </button>
        <span class="muted">{{ selected.length }} selected</span>
      </div>
      <div class="amazon-settings__buttons">
        <button
          class="button button--ghost"
          type="button"
          :disabled="!dirty || saving || browserRunActive || pendingKind !== null"
          @click="save"
        >
          {{ saving ? "Saving…" : "Save selection" }}
        </button>
        <button
          class="button"
          type="button"
          :disabled="!selected.length || saving || browserRunActive || pendingKind !== null"
          @click="start('amazon')"
        >
          {{ pendingKind === "amazon" ? "Collecting…" : "Scrape selected" }}
        </button>
      </div>
    </footer>

    <div class="run-summary">
      <span class="muted">Categories · {{ describe(latest('categories')) }}</span>
      <span class="muted">Products · {{ describe(latest('amazon')) }}</span>
    </div>
    <p v-if="error" class="alert alert--error">{{ error }}</p>
  </section>
</template>

<style scoped>
.amazon-settings {
  display: grid;
  gap: 1rem;
  padding: 1.15rem 1.25rem;
  margin-bottom: 1.25rem;
}

.amazon-settings__header,
.amazon-settings__footer,
.amazon-settings__buttons,
.selection-actions,
.run-summary {
  display: flex;
  align-items: center;
}

.amazon-settings__header,
.amazon-settings__footer {
  justify-content: space-between;
  gap: 1rem;
}

.amazon-settings__header h2 {
  font-size: 1rem;
}

.amazon-settings__header p {
  margin: 0.2rem 0 0;
  font-size: 0.82rem;
}

.category-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 0.5rem;
  max-height: 17rem;
  padding: 0.2rem;
  overflow-y: auto;
}

.category-option {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
  cursor: pointer;
  font-size: 0.86rem;
}

.category-option:has(input:checked) {
  border-color: color-mix(in srgb, var(--accent) 55%, var(--border));
  background: color-mix(in srgb, var(--accent) 9%, var(--surface));
}

.category-option input {
  width: 1rem;
  margin: 0;
  accent-color: var(--accent);
}

.selection-actions,
.amazon-settings__buttons,
.run-summary {
  gap: 0.75rem;
}

.text-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--accent);
  font-size: 0.82rem;
}

.text-button:disabled {
  color: var(--text-muted);
  cursor: not-allowed;
}

.selection-actions span,
.run-summary {
  font-size: 0.78rem;
}

.run-summary {
  flex-wrap: wrap;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border);
}

.amazon-settings__state {
  margin: 0;
  padding: 1rem 0;
  text-align: center;
}

@media (max-width: 720px) {
  .amazon-settings__header,
  .amazon-settings__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .amazon-settings__buttons .button {
    flex: 1;
    justify-content: center;
  }
}
</style>
