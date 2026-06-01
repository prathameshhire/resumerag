import { AlertTriangle, ArrowRight, CheckCircle2, Clipboard, FileCode2, FileText, Loader2, MapPin, Sparkles } from "lucide-react";
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
  onGenerated?: (response: TailorBulletsResponse) => void;
};

export function TailorPanel({ documentsRefreshKey, onGenerated }: TailorPanelProps) {
  const [targetRole, setTargetRole] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [bulletCount, setBulletCount] = useState(6);
  const [tone, setTone] = useState("technical");
  const [strictMode, setStrictMode] = useState(false);
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
      onGenerated?.(result);
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
  const hasGeneratedBullets = (response?.bullets.length ?? 0) > 0;
  const hasGeneratedSuggestions = hasGeneratedBullets || (response?.skill_suggestions.length ?? 0) > 0;

  return (
    <section id="tailor" className="section-shell section-padding mt-5">
      {hasGeneratedSuggestions ? (
        <a
          aria-label="Open LaTeX resume editor"
          className="fixed right-6 top-1/2 z-30 hidden -translate-y-1/2 items-center gap-3 rounded-lg border border-zinc-300 bg-white px-4 py-3 text-sm font-semibold text-zinc-950 shadow-xl shadow-zinc-300/50 transition hover:-translate-y-[calc(50%+2px)] hover:border-zinc-950 hover:bg-zinc-50 xl:flex"
          href="#/latex"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-zinc-950 text-white">
            <FileCode2 aria-hidden="true" size={17} />
          </span>
          <span className="grid text-left leading-tight">
            <span>Review in LaTeX</span>
            <span className="text-xs font-medium text-zinc-500">
              {response?.bullets.length ?? 0} bullets / {response?.skill_suggestions.length ?? 0} skills
            </span>
          </span>
          <ArrowRight aria-hidden="true" size={16} />
        </a>
      ) : null}

      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="section-heading">
          <div className="icon-tile border-emerald-200 bg-emerald-50 text-emerald-700">
          <Sparkles aria-hidden="true" size={21} />
        </div>
        <div>
            <p className="eyebrow">Generation</p>
          <h2 className="text-lg font-semibold text-zinc-950">Tailored Bullets</h2>
          <p className="mt-1 text-sm text-zinc-600">Generate grounded resume bullets with source evidence</p>
        </div>
      </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-semibold text-zinc-700">
            {documentCount} indexed docs
          </span>
          <span className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
            {strictMode ? "Strict gate" : "Draft mode"}
          </span>
        </div>
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="field-label">
            Target Role
            <input
              className="field-control"
              placeholder="Backend Engineer"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
            />
          </label>

          <label className="field-label">
            Company
            <input
              className="field-control"
              placeholder="Optional"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
            />
          </label>
        </div>

        <label className="field-label">
          Job Description
          <textarea
            className="field-control min-h-52 resize-y leading-6"
            placeholder="Paste the job description here"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
          />
        </label>

        <div className="grid gap-4 md:grid-cols-[120px_1fr_120px_auto]">
          <label className="field-label">
            Bullets
            <input
              className="field-control"
              min={1}
              max={8}
              type="number"
              value={bulletCount}
              onChange={(event) => setBulletCount(Number(event.target.value))}
            />
          </label>

          <label className="field-label">
            Tone
            <select
              className="field-control"
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

          <label className="field-label">
            Top K
            <input
              className="field-control"
              min={1}
              max={12}
              type="number"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
          </label>

          <label className="flex items-end gap-2 pb-2 text-sm font-semibold text-zinc-800">
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
          className={isGenerating ? "primary-button skeuo-loading-button" : "primary-button"}
          disabled={isGenerating || isCheckingDocuments || documentCount === 0}
        >
          {isGenerating ? <Loader2 aria-hidden="true" className="animate-spin" size={16} /> : <Sparkles aria-hidden="true" size={16} />}
          {isGenerating ? "Generating" : isCheckingDocuments ? "Checking Documents" : "Generate Tailored Bullets"}
        </button>
      </form>

      {!isCheckingDocuments && documentCount === 0 ? (
        <div className="empty-state mt-4">
          Upload indexed experience documents before tailoring bullets.
        </div>
      ) : null}

      {isGenerating ? (
        <div className="status-note skeuo-progress-note mt-4 flex items-center gap-3 border-emerald-200 bg-emerald-50 text-emerald-900">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          <span>Retrieving evidence and waiting for the local model</span>
        </div>
      ) : null}

      {error ? <div className="status-note mt-4 border-red-200 bg-red-50 text-red-900">{error}</div> : null}

      {response ? (
        <div className="mt-6 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">Generated Bullets</h3>
              {hasGeneratedBullets ? (
                <div className="flex flex-wrap gap-2">
                  <a className="secondary-button xl:hidden" href="#/latex">
                    <FileCode2 aria-hidden="true" size={15} />
                    Open LaTeX Editor
                  </a>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => copyText(allBulletsText, "all")}
                  >
                    <Clipboard aria-hidden="true" size={15} />
                    {copied === "all" ? "Copied" : "Copy All"}
                  </button>
                </div>
              ) : null}
            </div>

            {response.bullets.length === 0 ? (
              <div className="empty-state">
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

            {response.skill_suggestions.length > 0 ? (
              <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50/70 p-4">
                <div className="mb-3 text-sm font-semibold text-emerald-950">JD-mentioned skills for LaTeX</div>
                <div className="flex flex-wrap gap-2">
                  {response.skill_suggestions.map((skill) => (
                    <span key={`${skill.category}-${skill.skill}`} className="rounded-md border border-emerald-200 bg-white px-2 py-1 text-xs font-semibold text-emerald-900">
                      {skill.category}: {skill.skill}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {response.rejected_bullets.length > 0 ? (
              <div className="status-note mt-4 border-red-200 bg-red-50">
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-red-900">
                  <AlertTriangle aria-hidden="true" size={16} />
                  Rejected by validator
                </div>
                <div className="space-y-3">
                  {response.rejected_bullets.map((rejected, index) => (
                    <div key={`${rejected.bullet}-${index}`} className="text-sm text-red-950">
                      <p className="font-medium">{rejected.bullet}</p>
                      <p className="mt-1 text-xs leading-5 text-red-800">{rejected.reasons.join(" ")}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">Retrieved Evidence</h3>
            <div className="space-y-3">
              {response.retrieved_context.map((result) => (
                <article key={result.chunk_id} className="subtle-card p-4">
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
    <article className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm shadow-zinc-200/70">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-zinc-950 text-xs font-semibold text-white">
            {index + 1}
          </span>
          <EvidenceBadge strength={bullet.evidence_strength} />
        </div>
        <button
          type="button"
          className="inline-flex h-8 items-center gap-2 rounded-md border border-zinc-300 bg-white px-2 text-xs font-semibold text-zinc-800 transition hover:bg-zinc-50"
          onClick={onCopy}
        >
          {copied ? <CheckCircle2 aria-hidden="true" size={14} /> : <Clipboard aria-hidden="true" size={14} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <p className="text-sm font-medium leading-6 text-zinc-950">{bullet.bullet}</p>

      <div className="mt-4 grid gap-2 text-xs text-zinc-600">
        <div className="rounded-md border border-violet-200 bg-violet-50 px-3 py-2 text-violet-950">
          <div className="mb-1 flex items-center gap-2 font-semibold text-violet-900">
            <MapPin aria-hidden="true" size={13} />
            Place in resume
          </div>
          <div>
            <span className="font-semibold">{bullet.placement.section}</span> -&gt; {bullet.placement.entry}
          </div>
          <div className="mt-1 text-violet-800">{bullet.placement.rationale}</div>
        </div>
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
