import { apiGet } from "./client";
import type { FullHealthResponse, HealthResponse } from "../types/health";

export function getHealth(signal?: AbortSignal) {
  return apiGet<HealthResponse>("/health", signal);
}

export function getFullHealth(signal?: AbortSignal) {
  return apiGet<FullHealthResponse>("/health/full", signal);
}
