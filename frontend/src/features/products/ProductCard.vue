<script setup lang="ts">
import { formatCount, formatPrice } from "@/shared/format";

import ScoreBadge from "./ScoreBadge.vue";
import TrendPill from "./TrendPill.vue";
import type { Product } from "./types";

defineProps<{ product: Product }>();
</script>

<template>
  <article class="card product">
    <div class="product__media">
      <img :src="product.image_url" :alt="product.title" loading="lazy" />
    </div>

    <div class="product__body">
      <header class="product__head">
        <div class="product__titles">
          <a :href="product.url" target="_blank" rel="noopener" class="product__title">
            {{ product.title }}
          </a>
          <p class="product__meta muted">
            {{ product.category }}
            <template v-if="product.bestseller_rank"> · #{{ product.bestseller_rank }}</template>
            · {{ product.asin }}
          </p>
        </div>
        <ScoreBadge :score="product.score?.score ?? null" :source="product.score?.source ?? null" />
      </header>

      <dl class="product__facts">
        <div>
          <dt>Price</dt>
          <dd>{{ formatPrice(product.price) }}</dd>
        </div>
        <div>
          <dt>Rating</dt>
          <dd>{{ product.rating ?? "—" }}</dd>
        </div>
        <div>
          <dt>Reviews</dt>
          <dd>{{ formatCount(product.reviews_count) }}</dd>
        </div>
        <div>
          <dt>Boost</dt>
          <dd>+{{ Math.round(product.score?.boost_score ?? 0) }}</dd>
        </div>
      </dl>

      <div class="product__footer">
        <TrendPill :trend="product.trend" />
        <p v-if="product.score" class="product__reasoning">{{ product.score.reasoning }}</p>
        <p v-else class="product__reasoning muted">Waiting for the next scoring pass.</p>
      </div>
    </div>
  </article>
</template>

<style scoped>
.product {
  display: grid;
  grid-template-columns: 116px 1fr;
  gap: 1rem;
  padding: 1rem;
}

.product__media {
  display: grid;
  place-items: center;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
  overflow: hidden;
}

.product__media img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  mix-blend-mode: multiply;
}

@media (prefers-color-scheme: dark) {
  .product__media img {
    mix-blend-mode: normal;
  }
}

.product__body {
  display: grid;
  gap: 0.75rem;
  align-content: start;
  min-width: 0;
}

.product__head {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.product__titles {
  flex: 1;
  min-width: 0;
}

.product__title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-weight: 600;
  color: var(--text);
}

.product__title:hover {
  color: var(--accent);
}

.product__meta {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
}

.product__facts {
  display: flex;
  flex-wrap: wrap;
  gap: 0 1.5rem;
  margin: 0;
}

.product__facts dt {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.product__facts dd {
  margin: 0;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.product__footer {
  display: grid;
  gap: 0.4rem;
}

.product__reasoning {
  margin: 0;
  font-size: 0.87rem;
  color: var(--text-muted);
}

@media (max-width: 560px) {
  .product {
    grid-template-columns: 1fr;
  }

  .product__media {
    max-width: 140px;
  }
}
</style>
