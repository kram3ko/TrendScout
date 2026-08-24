export interface PastProduct {
  id: number;
  title: string;
  category: string;
  keywords: string;
  note: string | null;
  created_at: string;
}

export interface PastProductDraft {
  title: string;
  category: string;
  keywords: string;
  note: string | null;
}

export interface CsvImportReport {
  imported: number;
  skipped: { line: number; error: string }[];
}
