<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import { ApiError } from "@/shared/http";

import AmazonCategoryControls from "./AmazonCategoryControls.vue";
import ProductCard from "./ProductCard.vue";
import RunControls from "./RunControls.vue";
import { PAGE_SIZE, fetchCategories, fetchProducts } from "./api";
import type { Product, ProductFilters, ProductSort } from "./types";

const SORT_OPTIONS: { value: ProductSort; label: string }[] = [
  { value: "score", label: "Highest score" },
  { value: "rank", label: "Bestseller rank" },
  { value: "recent", label: "Recently updated" },
];
const SEARCH_DEBOUNCE_MS = 300;

const filters = reactive<ProductFilters>({ category: null, search: "", sort: "score" });
const products = ref<Product[]>([]);
const total = ref(0);
const offset = ref(0);
const categories = ref<string[]>([]);
const loading = ref(true);
const error = ref("");

const pageCount = computed(() => Math.max(Math.ceil(total.value / PAGE_SIZE), 1));
const page = computed(() => Math.floor(offset.value / PAGE_SIZE) + 1);

async function load(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const result = await fetchProducts(filters, offset.value);
    products.value = result.items;
    total.value = result.total;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "Could not load products";
  } finally {
    loading.value = false;
  }
}

async function loadCategories(): Promise<void> {
  try {
    categories.value = await fetchCategories();
  } catch {
    categories.value = [];
  }
}

async function refreshDashboard(): Promise<void> {
  await Promise.all([load(), loadCategories()]);
}

let debounce: number | undefined;
watch(
  () => ({ ...filters }),
  () => {
    offset.value = 0;
    window.clearTimeout(debounce);
    debounce = window.setTimeout(load, SEARCH_DEBOUNCE_MS);
  },
);
watch(offset, load);

function turnPage(delta: number): void {
  offset.value = Math.max(offset.value + delta * PAGE_SIZE, 0);
}

void refreshDashboard();
</script>

<template>
  <section class="head">
    <div>
      <h1>Product shortlist</h1>
      <p class="muted">{{ total }} product(s) collected from Amazon Best Sellers.</p>
    </div>
  </section>

  <RunControls @finished="refreshDashboard" />
  <AmazonCategoryControls @finished="refreshDashboard" />

  <section class="filters card">
    <label class="field">
      <span>Search</span>
      <input v-model="filters.search" placeholder="Title contains…" />
    </label>
    <label class="field">
      <span>Category</span>
      <select v-model="filters.category">
        <option :value="null">All categories</option>
        <option v-for="category in categories" :key="category" :value="category">
          {{ category }}
        </option>
      </select>
    </label>
    <label class="field">
      <span>Sort by</span>
      <select v-model="filters.sort">
        <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
    </label>
  </section>

  <p v-if="error" class="alert alert--error">{{ error }}</p>

  <p v-else-if="loading" class="muted state">Loading…</p>

  <p v-else-if="!products.length" class="card state">
    Nothing here yet — run <strong>Scrape Amazon</strong> to fill the shortlist.
  </p>

  <div v-else class="grid">
    <ProductCard v-for="product in products" :key="product.id" :product="product" />
  </div>

  <nav v-if="pageCount > 1" class="pager">
    <button class="button button--ghost" type="button" :disabled="page === 1" @click="turnPage(-1)">
      Previous
    </button>
    <span class="muted">Page {{ page }} of {{ pageCount }}</span>
    <button
      class="button button--ghost"
      type="button"
      :disabled="page >= pageCount"
      @click="turnPage(1)"
    >
      Next
    </button>
  </nav>
</template>

<style scoped>
.head {
  margin-bottom: 1.25rem;
}

.head h1 {
  font-size: 1.4rem;
}

.head p {
  margin: 0.25rem 0 0;
  font-size: 0.9rem;
}

.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 1rem;
}

.state {
  padding: 2rem;
  text-align: center;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

@media (max-width: 720px) {
  .filters {
    grid-template-columns: 1fr;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
