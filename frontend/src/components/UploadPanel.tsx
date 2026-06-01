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
    <section className="section-shell section-padding">
      <div className="mb-5 section-heading">
        <div className="icon-tile border-sky-200 bg-sky-50 text-sky-700">
          <FileUp aria-hidden="true" size={21} />
        </div>
        <div>
          <p className="eyebrow">Evidence intake</p>
          <h2 className="text-lg font-semibold text-zinc-950">Upload Experience</h2>
          <p className="mt-1 text-sm text-zinc-600">Index local documents as Markdown chunks</p>
        </div>
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit}>
        <label className="field-label">
          File
          <input
            className="block w-full min-w-0 rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition file:mr-3 file:rounded-md file:border-0 file:bg-zinc-950 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
            type="file"
            accept=".pdf,.docx,.md,.txt"
            onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
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
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="field-label">
            Title
            <input
              className="field-control"
              placeholder="Optional"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>

          <label className="field-label">
            Description
            <input
              className="field-control"
              placeholder="Optional"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
        </div>

        <button
          type="submit"
          className="primary-button"
          disabled={isUploading}
        >
          {isUploading ? <Loader2 aria-hidden="true" className="animate-spin" size={16} /> : <FileUp aria-hidden="true" size={16} />}
          {isUploading ? "Indexing" : "Upload and Index"}
        </button>
      </form>

      {result ? (
        <div className="status-note mt-4 border-emerald-200 bg-emerald-50 text-emerald-900">
          Indexed {result.filename} with {result.chunks_created} chunks.
        </div>
      ) : null}

      {isUploading ? (
        <div className="status-note mt-4 flex items-center gap-2 border-sky-200 bg-sky-50 text-sky-900">
          <Loader2 aria-hidden="true" className="animate-spin" size={16} />
          Converting, chunking, embedding, and storing vectors
        </div>
      ) : null}

      {error ? <div className="status-note mt-4 border-red-200 bg-red-50 text-red-900">{error}</div> : null}
    </section>
  );
}
