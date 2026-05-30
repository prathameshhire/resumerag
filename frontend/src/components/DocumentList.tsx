import { FileText, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { deleteDocument, getDocuments } from "../api/documents";
import type { DocumentListItem } from "../types/document";

type DocumentListProps = {
  refreshKey: number;
};

export function DocumentList({ refreshKey }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function loadDocuments(signal?: AbortSignal) {
    setIsLoading(true);
    setError(null);

    try {
      setDocuments(await getDocuments(signal));
    } catch (err) {
      if (!signal?.aborted) {
        setError(err instanceof Error ? err.message : "Could not load documents.");
      }
    } finally {
      if (!signal?.aborted) {
        setIsLoading(false);
      }
    }
  }

  async function handleDelete(documentId: string) {
    setDeletingId(documentId);
    setError(null);

    try {
      await deleteDocument(documentId);
      setDocuments((current) => current.filter((document) => document.id !== documentId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete document.");
    } finally {
      setDeletingId(null);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    loadDocuments(controller.signal);

    return () => controller.abort();
  }, [refreshKey]);

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-100 text-emerald-700">
            <FileText aria-hidden="true" size={21} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-zinc-950">Indexed Documents</h2>
            <p className="mt-1 text-sm text-zinc-600">Stored metadata and searchable chunks</p>
          </div>
        </div>
        <button
          type="button"
          aria-label="Refresh documents"
          title="Refresh documents"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-zinc-200 bg-white text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
          onClick={() => loadDocuments()}
        >
          <RefreshCw aria-hidden="true" size={16} />
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-4 text-sm text-zinc-600">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          Loading documents
        </div>
      ) : null}

      {!isLoading && documents.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-600">
          No experience documents indexed yet. Try a synthetic file from sample_data/experience.
        </div>
      ) : null}

      {!isLoading && documents.length > 0 ? (
        <div className="space-y-3">
          {documents.map((document) => (
            <article key={document.id} className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-950">{document.filename}</h3>
                  <p className="mt-1 text-xs text-zinc-500">
                    {document.chunks_count} chunks | {formatLabel(document.source_type)} | {formatLabel(document.category)}
                  </p>
                </div>
                <button
                  type="button"
                  aria-label={`Delete ${document.filename}`}
                  title={`Delete ${document.filename}`}
                  className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-zinc-200 bg-white text-zinc-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={deletingId === document.id}
                  onClick={() => handleDelete(document.id)}
                >
                  {deletingId === document.id ? <Loader2 aria-hidden="true" className="animate-spin" size={16} /> : <Trash2 aria-hidden="true" size={16} />}
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {error ? <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">{error}</div> : null}
    </section>
  );
}

function formatLabel(value: string | null) {
  if (!value) {
    return "Uncategorized";
  }

  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
