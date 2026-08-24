export type TrendDirection = "rising" | "flat" | "falling" | "unknown";
export type ProductSort = "score" | "rank" | "recent";

export interface Trend {
  keyword: string;
  direction: TrendDirection;
  latest_value: number | null;
  points_count: number;
  collected_at: string;
}

export interface Score {
  score: number;
  reasoning: string;
  boost_score: number;
  source: string;
  scored_at: string;
}

export interface Product {
  id: number;
  asin: string;
  title: string;
  category: string;
  price: number | null;
  rating: number | null;
  reviews_count: number | null;
  url: string;
  image_url: string;
  bestseller_rank: number | null;
  updated_at: string;
  score: Score | null;
  trend: Trend | null;
}

export interface ProductPage {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductFilters {
  category: string | null;
  search: string;
  sort: ProductSort;
}

export type RunKind = "amazon" | "categories" | "trends";
export type RunStatus = "running" | "success" | "blocked" | "failed";

export interface Run {
  id: number;
  kind: RunKind;
  status: RunStatus;
  items_collected: number;
  detail: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface AmazonCategory {
  slug: string;
  name: string;
  enabled: boolean;
}
