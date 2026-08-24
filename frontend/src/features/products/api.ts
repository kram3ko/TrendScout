import { request } from "@/shared/http";

import type { AmazonCategory, ProductFilters, ProductPage, Run, RunKind } from "./types";

export const PAGE_SIZE = 24;

export function fetchProducts(filters: ProductFilters, offset: number): Promise<ProductPage> {
  const params = new URLSearchParams({
    sort: filters.sort,
    limit: String(PAGE_SIZE),
    offset: String(offset),
  });
  if (filters.category) params.set("category", filters.category);
  if (filters.search.trim()) params.set("search", filters.search.trim());
  return request<ProductPage>(`/products?${params.toString()}`);
}

export const fetchCategories = (): Promise<string[]> => request<string[]>("/products/categories");

export const fetchRuns = (): Promise<Run[]> => request<Run[]>("/runs");

export const triggerRun = (kind: RunKind): Promise<{ task_id: string }> =>
  request<{ task_id: string }>(`/runs/${kind}`, { method: "POST" });

export const fetchAmazonCategories = (): Promise<AmazonCategory[]> =>
  request<AmazonCategory[]>("/amazon-categories");

export const saveAmazonCategories = (slugs: string[]): Promise<AmazonCategory[]> =>
  request<AmazonCategory[]>("/amazon-categories", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slugs }),
  });
