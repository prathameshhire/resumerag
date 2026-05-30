import { API_BASE_URL } from "./client";
import type { TailorBulletsRequest, TailorBulletsResponse } from "../types/tailor";

export async function generateTailoredBullets(request: TailorBulletsRequest): Promise<TailorBulletsResponse> {
  const response = await fetch(`${API_BASE_URL}/tailor/bullets`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<TailorBulletsResponse>;
}

async function getErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}
