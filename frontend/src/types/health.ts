export type HealthResponse = {
  status: string;
  backend: boolean;
};

export type ComponentHealth = {
  ok: boolean;
  message?: string | null;
};

export type EmbeddingModelHealth = ComponentHealth & {
  model: string;
  dimension: number;
};

export type OllamaHealth = ComponentHealth & {
  base_url: string;
  model: string;
  model_available: boolean;
};

export type FullHealthResponse = {
  backend: ComponentHealth;
  database: ComponentHealth;
  pgvector: ComponentHealth;
  embedding_model: EmbeddingModelHealth;
  ollama: OllamaHealth;
};
