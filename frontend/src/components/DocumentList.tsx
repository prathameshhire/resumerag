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
    <section className="section-shell section-padding">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="section-heading">
          <div className="icon-tile border-emerald-200 bg-emerald-50 text-emerald-700">
            <FileText aria-hidden="true" size={21} />
          </div>
          <div>
            <p className="eyebrow">Library</p>
            <h2 className="text-lg font-semibold text-zinc-950">Indexed Documents</h2>
            <p className="mt-1 text-sm text-zinc-600">Stored metadata and searchable chunks</p>
          </div>
        </div>
        <button
          type="button"
          aria-label="Refresh documents"
          title="Refresh documents"
          className="icon-button"
          onClick={() => loadDocuments()}
        >
          <RefreshCw aria-hidden="true" size={16} />
        </button>
      </div>

      {isLoading ? (
        <div className="subtle-card flex items-center gap-2 px-4 py-4 text-sm text-zinc-600">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          Loading documents
        </div>
      ) : null}

      {!isLoading && documents.length === 0 ? (
        <div className="empty-state">
          No experience documents indexed yet. Try a synthetic file from sample_data/experience.
        </div>
      ) : null}

      {!isLoading && documents.length > 0 ? (
        <div className="space-y-3">
          {documents.map((document) => (
            <article key={document.id} className="subtle-card p-4 transition hover:border-zinc-300 hover:bg-white">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h3 className="truncate text-sm font-semibold text-zinc-950">{document.filename}</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-semibold text-zinc-700">
                      {document.chunks_count} chunks
                    </span>
                    <span className="rounded-md border border-sky-200 bg-sky-50 px-2 py-1 text-xs font-semibold text-sky-800">
                      {formatLabel(document.source_type)}
                    </span>
                    <span className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-800">
                      {formatLabel(document.category)}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  aria-label={`Delete ${document.filename}`}
                  title={`Delete ${document.filename}`}
                  className="icon-button shrink-0 hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-50"
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

      {error ? <div className="status-note mt-4 border-red-200 bg-red-50 text-red-900">{error}</div> : null}
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
