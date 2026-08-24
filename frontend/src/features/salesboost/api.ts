import { postJson, request } from "@/shared/http";

import type { CsvImportReport, PastProduct, PastProductDraft } from "./types";

export const fetchPastProducts = (): Promise<PastProduct[]> =>
  request<PastProduct[]>("/past-products");

export const createPastProduct = (draft: PastProductDraft): Promise<PastProduct> =>
  postJson<PastProduct>("/past-products", draft);

export const deletePastProduct = (id: number): Promise<void> =>
  request<void>(`/past-products/${id}`, { method: "DELETE" });

export function importPastProducts(file: File): Promise<CsvImportReport> {
  const body = new FormData();
  body.append("file", file);
  return request<CsvImportReport>("/past-products/import", { method: "POST", body });
}
