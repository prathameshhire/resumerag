import { API_BASE_URL } from "./client";

export async function exportLatexPdf(latex: string, filename = "resume.pdf"): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/latex/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ latex, filename }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.blob();
}

async function getErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}
