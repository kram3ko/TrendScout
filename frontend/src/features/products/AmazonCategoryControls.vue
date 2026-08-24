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
const SELECTED_CATEGORY_PREVIEW_LIMIT = 5;

const emit = defineEmits<{ finished: [] }>();

const categories = ref<AmazonCategory[]>([]);
const selected = ref<string[]>([]);
const loading = ref(true);
const saving = ref(false);
const expanded = ref(false);
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
const selectedCategoryNames = computed(() => {
  const selectedSlugs = new Set(selected.value);
  return categories.value
    .filter((category) => selectedSlugs.has(category.slug))
    .map((category) => category.name);
});
const visibleSelectedCategoryNames = computed(() =>
  selectedCategoryNames.value.slice(0, SELECTED_CATEGORY_PREVIEW_LIMIT),
);
const hiddenSelectedCategoryCount = computed(() =>
  Math.max(selectedCategoryNames.value.length - SELECTED_CATEGORY_PREVIEW_LIMIT, 0),
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
      <div class="amazon-settings__header-actions">
        <span v-if="!loading && categories.length" class="selection-count">
          {{ selected.length }} of {{ categories.length }} selected
        </span>
        <button
          class="button button--ghost toggle-button"
          type="button"
          :aria-expanded="expanded"
          aria-controls="amazon-category-panel"
          @click="expanded = !expanded"
        >
          {{ expanded ? "Hide categories" : "Show categories" }}
          <span class="toggle-button__icon" :data-expanded="expanded" aria-hidden="true">⌄</span>
        </button>
      </div>
    </header>

    <div
      v-if="!expanded && selectedCategoryNames.length"
      class="selected-preview"
      aria-label="Selected Amazon categories"
    >
      <span
        v-for="categoryName in visibleSelectedCategoryNames"
        :key="categoryName"
        class="category-chip"
        :title="categoryName"
      >
        {{ categoryName }}
      </span>
      <button
        v-if="hiddenSelectedCategoryCount"
        class="category-chip category-chip--more"
        type="button"
        @click="expanded = true"
      >
        +{{ hiddenSelectedCategoryCount }} more · show all
      </button>
    </div>

    <div v-if="expanded" id="amazon-category-panel" class="category-panel">
      <div class="category-panel__toolbar">
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
        </div>
        <button
          class="text-button"
          type="button"
          :disabled="browserRunActive || pendingKind !== null || saving"
          @click="start('categories')"
        >
          {{ categories.length ? "Refresh from Amazon" : "Discover categories" }}
        </button>
      </div>

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
    </div>

    <footer class="amazon-settings__footer">
      <span class="muted footer-selection">{{ selected.length }} departments ready to scrape</span>
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
.amazon-settings__header-actions,
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

.amazon-settings__header-actions {
  justify-content: flex-end;
  gap: 0.75rem;
}

.amazon-settings__header h2 {
  font-size: 1rem;
}

.amazon-settings__header p {
  margin: 0.2rem 0 0;
  font-size: 0.82rem;
}

.selection-count {
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  background: var(--surface-muted);
  color: var(--text-muted);
  font-size: 0.75rem;
  white-space: nowrap;
}

.selected-preview {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.category-chip {
  max-width: 15rem;
  padding: 0.16rem 0.42rem;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--border));
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 12%, var(--surface));
  color: var(--accent);
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1.2;
  text-overflow: ellipsis;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.category-chip--more {
  flex: none;
  cursor: pointer;
  font-family: inherit;
}

.category-chip--more:hover,
.category-chip--more:focus-visible {
  background: color-mix(in srgb, var(--accent) 18%, var(--surface));
}

.toggle-button {
  gap: 0.4rem;
  white-space: nowrap;
}

.toggle-button__icon {
  display: inline-block;
  font-size: 1rem;
  line-height: 0.8;
  transform: rotate(0deg);
  transition: transform 160ms ease;
}

.toggle-button__icon[data-expanded="true"] {
  transform: rotate(180deg);
}

.category-panel {
  display: grid;
  gap: 0.75rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border);
}

.category-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
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

.run-summary,
.footer-selection {
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

  .amazon-settings__header-actions,
  .amazon-settings__buttons {
    width: 100%;
  }

  .amazon-settings__header-actions {
    justify-content: space-between;
  }

  .amazon-settings__buttons .button {
    flex: 1;
    justify-content: center;
  }
}
</style>
