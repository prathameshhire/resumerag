import { Loader2, Search } from "lucide-react";
import { FormEvent, useState } from "react";

import { searchDocuments } from "../api/search";
import type { SearchResult } from "../types/search";

const sourceTypes = [
  { label: "All Sources", value: "" },
  { label: "Resume", value: "resume" },
  { label: "Project Notes", value: "project_notes" },
  { label: "Work Experience", value: "work_experience" },
  { label: "GitHub README", value: "github_readme" },
  { label: "Achievement Bank", value: "achievement_bank" },
  { label: "Other", value: "other" },
];

const categories = [
  { label: "All Categories", value: "" },
  { label: "Backend", value: "backend" },
  { label: "Data", value: "data" },
  { label: "ML Infrastructure", value: "ml_infra" },
  { label: "Full Stack", value: "fullstack" },
  { label: "Academic", value: "academic" },
  { label: "Leadership", value: "leadership" },
  { label: "Other", value: "other" },
];

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(8);
  const [sourceType, setSourceType] = useState("");
  const [category, setCategory] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setHasSearched(true);

    if (!query.trim()) {
      setResults([]);
      setError("Enter a search query.");
      return;
    }

    setIsSearching(true);

    try {
      const response = await searchDocuments({
        query,
        top_k: topK,
        filters: {
          ...(sourceType ? { source_type: sourceType } : {}),
          ...(category ? { category } : {}),
        },
      });
      setResults(response.results);
    } catch (err) {
      setResults([]);
      setError(formatSearchError(err));
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <section id="search" className="section-shell section-padding mt-5">
      <div className="mb-5 section-heading">
        <div className="icon-tile border-indigo-200 bg-indigo-50 text-indigo-700">
          <Search aria-hidden="true" size={21} />
        </div>
        <div>
          <p className="eyebrow">Retrieval lab</p>
          <h2 className="text-lg font-semibold text-zinc-950">Search Experience Context</h2>
          <p className="mt-1 text-sm text-zinc-600">Retrieve embedded chunks from uploaded documents</p>
        </div>
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit}>
        <label className="field-label">
          Query
          <input
            className="field-control"
            placeholder="FastAPI PostgreSQL authentication"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>

        <div className="grid gap-4 md:grid-cols-[1fr_1fr_120px]">
          <label className="field-label">
            Source Type
            <select
              className="field-control"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value)}
            >
              {sourceTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field-label">
            Category
            <select
              className="field-control"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              {categories.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field-label">
            Top K
            <input
              className="field-control"
              min={1}
              max={20}
              type="number"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
          </label>
        </div>

        <button
          type="submit"
          className="primary-button"
          disabled={isSearching}
        >
          {isSearching ? <Loader2 aria-hidden="true" className="animate-spin" size={16} /> : <Search aria-hidden="true" size={16} />}
          {isSearching ? "Searching" : "Search Chunks"}
        </button>
      </form>

      {error ? <div className="status-note mt-4 border-red-200 bg-red-50 text-red-900">{error}</div> : null}

      {isSearching ? (
        <div className="status-note mt-4 flex items-center gap-2 border-indigo-200 bg-indigo-50 text-indigo-900">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          Embedding query and searching stored chunks
        </div>
      ) : null}

      {!error && hasSearched && !isSearching && results.length === 0 ? (
        <div className="empty-state mt-4">
          No matching chunks found.
        </div>
      ) : null}

      {results.length > 0 ? (
        <div className="mt-5 space-y-3">
          {results.map((result) => (
            <article key={result.chunk_id} className="subtle-card p-4 transition hover:border-zinc-300 hover:bg-white">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-950">
                    #{result.rank} {result.source}
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500">{result.section_title ?? "Untitled section"}</p>
                </div>
                <span className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-semibold text-zinc-700">
                  {formatScore(result.similarity_score)}
                </span>
              </div>
              <p className="line-clamp-6 whitespace-pre-wrap text-sm leading-6 text-zinc-700">{result.chunk_text}</p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function formatScore(score: number) {
  return `${Math.round(score * 100)}% match`;
}

function formatSearchError(err: unknown) {
  const message = err instanceof Error ? err.message : "Search failed.";
  if (message.toLowerCase().includes("upload documents first")) {
    return "No indexed evidence found. Upload an experience document first.";
  }
  return message;
}
