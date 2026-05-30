import type { SearchResult } from "./search";

export type TailorBulletsRequest = {
  job_description: string;
  target_role?: string | null;
  company_name?: string | null;
  bullet_count?: number;
  tone?: string;
  strict_mode?: boolean;
  top_k?: number;
};

export type TailoredBullet = {
  bullet: string;
  matched_requirement: string;
  evidence_strength: "high" | "medium" | "low" | string;
  source_chunk_ids: string[];
  notes: string | null;
};

export type TailorBulletsResponse = {
  query_id: string;
  target_role: string | null;
  company_name: string | null;
  bullets: TailoredBullet[];
  retrieved_context: SearchResult[];
  warnings: string[];
};
