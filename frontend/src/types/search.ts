export type SearchFilters = {
  source_type?: string;
  category?: string;
};

export type SearchRequest = {
  query: string;
  top_k?: number;
  filters?: SearchFilters;
};

export type SearchResult = {
  chunk_id: string;
  document_id: string;
  source: string;
  chunk_text: string;
  section_title: string | null;
  similarity_score: number;
  rank: number;
  metadata: Record<string, unknown>;
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
};
