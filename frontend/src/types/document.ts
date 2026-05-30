export type DocumentListItem = {
  id: string;
  filename: string;
  source_type: string | null;
  category: string | null;
  chunks_count: number;
  created_at: string;
};

export type DocumentUploadResponse = {
  document_id: string;
  filename: string;
  chunks_created: number;
  status: string;
};
