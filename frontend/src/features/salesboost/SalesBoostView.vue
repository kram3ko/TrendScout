<script setup lang="ts">
import { reactive, ref } from "vue";

import { formatDate } from "@/shared/format";
import { ApiError } from "@/shared/http";

import {
  createPastProduct,
  deletePastProduct,
  fetchAmazonCategories,
  fetchPastProducts,
  importPastProducts,
} from "./api";
import type {
  AmazonCategoryOption,
  CsvImportReport,
  PastProduct,
  PastProductDraft,
} from "./types";

const CSV_TEMPLATE = "title,category,keywords,note";

const items = ref<PastProduct[]>([]);
const categories = ref<AmazonCategoryOption[]>([]);
const loading = ref(true);
const error = ref("");
const report = ref<CsvImportReport | null>(null);
const uploading = ref(false);
const saving = ref(false);

const draft = reactive<PastProductDraft>({ title: "", category: "", keywords: "", note: null });

function report_error(caught: unknown, fallback: string): void {
  error.value = caught instanceof ApiError ? caught.message : fallback;
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    [items.value, categories.value] = await Promise.all([
      fetchPastProducts(),
      fetchAmazonCategories(),
    ]);
  } catch (caught) {
    report_error(caught, "Could not load past products");
  } finally {
    loading.value = false;
  }
}

async function submit(): Promise<void> {
  saving.value = true;
  error.value = "";
  try {
    await createPastProduct({ ...draft, note: draft.note || null });
    Object.assign(draft, { title: "", category: "", keywords: "", note: null });
    await load();
  } catch (caught) {
    report_error(caught, "Could not save the product");
  } finally {
    saving.value = false;
  }
}

async function upload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  uploading.value = true;
  error.value = "";
  report.value = null;
  try {
    report.value = await importPastProducts(file);
    await load();
  } catch (caught) {
    report_error(caught, "Could not import the file");
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function remove(id: number): Promise<void> {
  try {
    await deletePastProduct(id);
    await load();
  } catch (caught) {
    report_error(caught, "Could not delete the product");
  }
}

void load();
</script>

<template>
  <section class="head">
    <h1>Sales Boost</h1>
    <p class="muted">
      Products we already sold well. Anything on the shortlist that matches them by category or
      keywords earns extra points.
    </p>
  </section>

  <p v-if="error" class="alert alert--error">{{ error }}</p>

  <div class="layout">
    <form class="card panel" @submit.prevent="submit">
      <h2>Add manually</h2>

      <label class="field">
        <span>Title</span>
        <input v-model="draft.title" required maxlength="512" />
      </label>

      <label class="field">
        <span>Category</span>
        <select v-model="draft.category" required :disabled="loading || !categories.length">
          <option disabled value="">Select an Amazon category</option>
          <option v-for="category in categories" :key="category.slug" :value="category.name">
            {{ category.name }}
          </option>
        </select>
      </label>
      <p v-if="!loading && !categories.length" class="muted hint">
        Discover Amazon categories on the dashboard first.
      </p>

      <label class="field">
        <span>Keywords</span>
        <input v-model="draft.keywords" maxlength="512" placeholder="hose, watering, reel" />
      </label>

      <label class="field">
        <span>Note</span>
        <textarea v-model="draft.note" rows="2" maxlength="1024" />
      </label>

      <button class="button" type="submit" :disabled="saving">
        {{ saving ? "Saving…" : "Add product" }}
      </button>

      <hr />

      <h2>Import CSV</h2>
      <p class="muted hint">Columns: <code>{{ CSV_TEMPLATE }}</code></p>
      <input type="file" accept=".csv,text/csv" :disabled="uploading" @change="upload" />

      <div v-if="report" class="alert">
        Imported {{ report.imported }} row(s).
        <ul v-if="report.skipped.length" class="skipped">
          <li v-for="row in report.skipped" :key="row.line">
            Line {{ row.line }} — {{ row.error }}
          </li>
        </ul>
      </div>
    </form>

    <section class="card panel">
      <h2>Our past winners ({{ items.length }})</h2>

      <p v-if="loading" class="muted">Loading…</p>
      <p v-else-if="!items.length" class="muted">
        Nothing yet. Add a product or import your history to start boosting.
      </p>

      <ul v-else class="list">
        <li v-for="item in items" :key="item.id">
          <div class="list__main">
            <strong>{{ item.title }}</strong>
            <p class="muted">
              {{ item.category }}
              <template v-if="item.keywords"> · {{ item.keywords }}</template>
            </p>
            <p v-if="item.note" class="muted note">{{ item.note }}</p>
          </div>
          <div class="list__side">
            <span class="muted">{{ formatDate(item.created_at) }}</span>
            <button class="button button--ghost" type="button" @click="remove(item.id)">
              Remove
            </button>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.head {
  margin-bottom: 1.25rem;
  max-width: 62ch;
}

.head h1 {
  font-size: 1.4rem;
}

.head p {
  margin: 0.25rem 0 0;
  font-size: 0.9rem;
}

.layout {
  display: grid;
  grid-template-columns: minmax(300px, 380px) 1fr;
  gap: 1.25rem;
  align-items: start;
}

.panel {
  display: grid;
  gap: 0.85rem;
  padding: 1.25rem;
}

.panel h2 {
  font-size: 1rem;
}

hr {
  width: 100%;
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.25rem 0;
}

.hint {
  margin: -0.5rem 0 0;
  font-size: 0.8rem;
}

.skipped {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  font-size: 0.82rem;
}

.list {
  display: grid;
  gap: 0.75rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.list li {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.85rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.list__main p {
  margin: 0.15rem 0 0;
  font-size: 0.82rem;
}

.note {
  font-style: italic;
}

.list__side {
  display: grid;
  justify-items: end;
  gap: 0.4rem;
  font-size: 0.78rem;
  flex: none;
}

@media (max-width: 860px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
