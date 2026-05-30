import { API_BASE_URL, apiGet } from "./client";
import type { DocumentListItem, DocumentUploadResponse } from "../types/document";

export type UploadDocumentInput = {
  file: File;
  sourceType?: string;
  category?: string;
  title?: string;
  description?: string;
};

export function getDocuments(signal?: AbortSignal) {
  return apiGet<DocumentListItem[]>("/documents", signal);
}

export async function uploadDocument(input: UploadDocumentInput): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", input.file);
  appendOptional(formData, "source_type", input.sourceType);
  appendOptional(formData, "category", input.category);
  appendOptional(formData, "title", input.title);
  appendOptional(formData, "description", input.description);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<DocumentUploadResponse>;
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
}

function appendOptional(formData: FormData, key: string, value?: string) {
  if (value?.trim()) {
    formData.append(key, value.trim());
  }
}

async function getErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}
