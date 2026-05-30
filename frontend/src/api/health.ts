import { apiGet } from "./client";
import type { HealthResponse } from "../types/health";

export function getHealth(signal?: AbortSignal) {
  return apiGet<HealthResponse>("/health", signal);
}
