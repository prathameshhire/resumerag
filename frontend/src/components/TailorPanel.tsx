import { AlertTriangle, CheckCircle2, Clipboard, FileText, Loader2, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { getDocuments } from "../api/documents";
import { generateTailoredBullets } from "../api/tailor";
import type { SearchResult } from "../types/search";
import type { TailorBulletsResponse, TailoredBullet } from "../types/tailor";

const toneOptions = [
  { label: "Technical", value: "technical" },
  { label: "Concise", value: "concise" },
  { label: "Impact-driven", value: "impact-driven" },
];

type TailorPanelProps = {
  documentsRefreshKey: number;
};

export function TailorPanel({ documentsRefreshKey }: TailorPanelProps) {
  const [targetRole, setTargetRole] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [bulletCount, setBulletCount] = useState(6);
  const [tone, setTone] = useState("technical");
  const [strictMode, setStrictMode] = useState(true);
  const [topK, setTopK] = useState(8);
  const [response, setResponse] = useState<TailorBulletsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [documentCount, setDocumentCount] = useState(0);
  const [isCheckingDocuments, setIsCheckingDocuments] = useState(true);

  const contextById = useMemo(() => {
    const map = new Map<string, SearchResult>();
    response?.retrieved_context.forEach((result) => map.set(result.chunk_id, result));
    return map;
  }, [response]);

  useEffect(() => {
    const controller = new AbortController();
    setIsCheckingDocuments(true);

    getDocuments(controller.signal)
      .then((documents) => setDocumentCount(documents.length))
      .catch(() => setDocumentCount(0))
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsCheckingDocuments(false);
        }
      });

    return () => controller.abort();
  }, [documentsRefreshKey]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResponse(null);

    if (!jobDescription.trim()) {
      setError("Paste a job description first.");
      return;
    }

    if (!isCheckingDocuments && documentCount === 0) {
      setError("Upload an experience document before generating tailored bullets.");
      return;
    }

    setIsGenerating(true);

    try {
      const result = await generateTailoredBullets({
        job_description: jobDescription,
        target_role: targetRole || null,
        company_name: companyName || null,
        bullet_count: bulletCount,
        tone,
        strict_mode: strictMode,
        top_k: topK,
      });
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tailoring failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  async function copyText(text: string, key: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      window.setTimeout(() => setCopied(null), 1400);
    } catch {
      setError("Clipboard copy is not available in this browser.");
    }
  }

  const allBulletsText = response?.bullets.map((bullet) => `- ${bullet.bullet}`).join("\n") ?? "";

  return (
    <section id="tailor" className="mt-5 scroll-mt-4 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-100 text-emerald-700">
          <Sparkles aria-hidden="true" size={21} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Tailored Bullets</h2>
          <p className="mt-1 text-sm text-zinc-600">Generate grounded resume bullets with source evidence</p>
        </div>
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Target Role
            <input
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              placeholder="Backend Engineer"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
            />
          </label>

          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Company
            <input
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              placeholder="Optional"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
            />
          </label>
        </div>

        <label className="grid gap-2 text-sm font-medium text-zinc-800">
          Job Description
          <textarea
            className="min-h-48 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm leading-6 text-zinc-900"
            placeholder="Paste the job description here"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
          />
        </label>

        <div className="grid gap-4 md:grid-cols-[120px_1fr_120px_auto]">
          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Bullets
            <input
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              min={1}
              max={8}
              type="number"
              value={bulletCount}
              onChange={(event) => setBulletCount(Number(event.target.value))}
            />
          </label>

          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Tone
            <select
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              value={tone}
              onChange={(event) => setTone(event.target.value)}
            >
              {toneOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Top K
            <input
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              min={1}
              max={12}
              type="number"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
          </label>

          <label className="flex items-end gap-2 pb-2 text-sm font-medium text-zinc-800">
            <input
              checked={strictMode}
              className="h-4 w-4 rounded border-zinc-300 text-zinc-900"
              type="checkbox"
              onChange={(event) => setStrictMode(event.target.checked)}
            />
            Strict mode
          </label>
        </div>

        <button
          type="submit"
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-zinc-900 px-4 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          disabled={isGenerating || isCheckingDocuments || documentCount === 0}
        >
          {isGenerating ? <Loader2 aria-hidden="true" className="animate-spin" size={16} /> : <Sparkles aria-hidden="true" size={16} />}
          {isGenerating ? "Generating" : isCheckingDocuments ? "Checking Documents" : "Generate Tailored Bullets"}
        </button>
      </form>

      {!isCheckingDocuments && documentCount === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-4 py-6 text-center text-sm text-zinc-600">
          Upload indexed experience documents before tailoring bullets.
        </div>
      ) : null}

      {isGenerating ? (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          Retrieving evidence and waiting for the local model
        </div>
      ) : null}

      {error ? <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">{error}</div> : null}

      {response ? (
        <div className="mt-6 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">Generated Bullets</h3>
              {response.bullets.length > 0 ? (
                <button
                  type="button"
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-zinc-300 bg-white px-3 text-sm font-medium text-zinc-800 transition hover:bg-zinc-50"
                  onClick={() => copyText(allBulletsText, "all")}
                >
                  <Clipboard aria-hidden="true" size={15} />
                  {copied === "all" ? "Copied" : "Copy All"}
                </button>
              ) : null}
            </div>

            {response.warnings.length > 0 ? (
              <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <div className="mb-1 flex items-center gap-2 font-semibold">
                  <AlertTriangle aria-hidden="true" size={16} />
                  Warnings
                </div>
                <ul className="list-disc space-y-1 pl-5">
                  {response.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {response.bullets.length === 0 ? (
              <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-4 py-8 text-center text-sm text-zinc-600">
                Not enough evidence for grounded bullets.
              </div>
            ) : (
              <div className="space-y-3">
                {response.bullets.map((bullet, index) => (
                  <BulletCard
                    bullet={bullet}
                    copied={copied === `bullet-${index}`}
                    evidence={bullet.source_chunk_ids.map((chunkId) => contextById.get(chunkId)).filter(Boolean) as SearchResult[]}
                    index={index}
                    key={`${bullet.bullet}-${index}`}
                    onCopy={() => copyText(bullet.bullet, `bullet-${index}`)}
                  />
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">Retrieved Evidence</h3>
            <div className="space-y-3">
              {response.retrieved_context.map((result) => (
                <article key={result.chunk_id} className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <div className="min-w-0">
                      <h4 className="truncate text-sm font-semibold text-zinc-950">
                        #{result.rank} {result.source}
                      </h4>
                      <p className="mt-1 text-xs text-zinc-500">{result.section_title ?? "Untitled section"}</p>
                    </div>
                    <span className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-semibold text-zinc-700">
                      {formatScore(result.similarity_score)}
                    </span>
                  </div>
                  <p className="line-clamp-5 whitespace-pre-wrap text-sm leading-6 text-zinc-700">{result.chunk_text}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

type BulletCardProps = {
  bullet: TailoredBullet;
  copied: boolean;
  evidence: SearchResult[];
  index: number;
  onCopy: () => void;
};

function BulletCard({ bullet, copied, evidence, index, onCopy }: BulletCardProps) {
  return (
    <article className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-white text-xs font-semibold text-zinc-700">
            {index + 1}
          </span>
          <EvidenceBadge strength={bullet.evidence_strength} />
        </div>
        <button
          type="button"
          className="inline-flex h-8 items-center gap-2 rounded-md border border-zinc-300 bg-white px-2 text-xs font-medium text-zinc-800 transition hover:bg-zinc-50"
          onClick={onCopy}
        >
          {copied ? <CheckCircle2 aria-hidden="true" size={14} /> : <Clipboard aria-hidden="true" size={14} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <p className="text-sm leading-6 text-zinc-950">{bullet.bullet}</p>

      <div className="mt-4 grid gap-2 text-xs text-zinc-600">
        <div>
          <span className="font-semibold text-zinc-800">Requirement:</span> {bullet.matched_requirement}
        </div>
        {bullet.notes ? (
          <div>
            <span className="font-semibold text-zinc-800">Notes:</span> {bullet.notes}
          </div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {evidence.length > 0 ? (
          evidence.map((source) => (
            <span key={source.chunk_id} className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-700">
              <FileText aria-hidden="true" size={13} />
              #{source.rank} {source.source}
            </span>
          ))
        ) : (
          <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-900">No source references returned</span>
        )}
      </div>
    </article>
  );
}

function EvidenceBadge({ strength }: { strength: string }) {
  const normalized = strength.toLowerCase();
  const className =
    normalized === "high"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : normalized === "medium"
        ? "border-sky-200 bg-sky-50 text-sky-800"
        : "border-amber-200 bg-amber-50 text-amber-900";

  return <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${className}`}>{normalized} evidence</span>;
}

function formatScore(score: number) {
  return `${Math.round(score * 100)}% match`;
}
