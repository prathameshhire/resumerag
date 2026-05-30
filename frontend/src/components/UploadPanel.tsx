import { FileUp, Loader2 } from "lucide-react";
import { FormEvent, useState } from "react";

import { uploadDocument } from "../api/documents";
import type { DocumentUploadResponse } from "../types/document";

type UploadPanelProps = {
  onUploaded: () => void;
};

const sourceTypes = [
  { label: "Resume", value: "resume" },
  { label: "Project Notes", value: "project_notes" },
  { label: "Work Experience", value: "work_experience" },
  { label: "GitHub README", value: "github_readme" },
  { label: "Achievement Bank", value: "achievement_bank" },
  { label: "Other", value: "other" },
];

const categories = [
  { label: "Backend", value: "backend" },
  { label: "Data", value: "data" },
  { label: "ML Infrastructure", value: "ml_infra" },
  { label: "Full Stack", value: "fullstack" },
  { label: "Academic", value: "academic" },
  { label: "Leadership", value: "leadership" },
  { label: "Other", value: "other" },
];

export function UploadPanel({ onUploaded }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState("project_notes");
  const [category, setCategory] = useState("backend");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<DocumentUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setError(null);
    setResult(null);

    if (!file) {
      setError("Choose a PDF, DOCX, Markdown, or TXT file first.");
      return;
    }

    setIsUploading(true);

    try {
      const uploadResult = await uploadDocument({
        file,
        sourceType,
        category,
        title,
        description,
      });
      setResult(uploadResult);
      setFile(null);
      setTitle("");
      setDescription("");
      form.reset();
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-sky-100 text-sky-700">
          <FileUp aria-hidden="true" size={21} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Upload Experience</h2>
          <p className="mt-1 text-sm text-zinc-600">Index local documents as Markdown chunks</p>
        </div>
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit}>
        <label className="grid gap-2 text-sm font-medium text-zinc-800">
          File
          <input
            className="block w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 file:mr-3 file:rounded-md file:border-0 file:bg-zinc-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white"
            type="file"
            accept=".pdf,.docx,.md,.txt"
            onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Source Type
            <select
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
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

          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Category
            <select
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
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
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Title
            <input
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              placeholder="Optional"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>

          <label className="grid gap-2 text-sm font-medium text-zinc-800">
            Description
            <input
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900"
              placeholder="Optional"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
        </div>

        <button
          type="submit"
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-zinc-900 px-4 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          disabled={isUploading}
        >
          {isUploading ? <Loader2 aria-hidden="true" className="animate-spin" size={16} /> : <FileUp aria-hidden="true" size={16} />}
          {isUploading ? "Indexing" : "Upload and Index"}
        </button>
      </form>

      {result ? (
        <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          Indexed {result.filename} with {result.chunks_created} chunks.
        </div>
      ) : null}

      {isUploading ? (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          Converting, chunking, embedding, and storing vectors
        </div>
      ) : null}

      {error ? <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">{error}</div> : null}
    </section>
  );
}
