import { ArrowRight, FileCheck2, FileText, LockKeyhole, Search, ShieldCheck, Sparkles, UploadCloud } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { DocumentList } from "./components/DocumentList";
import { HealthChecklist } from "./components/HealthChecklist";
import { LatexResumeEditor } from "./components/LatexResumeEditor";
import { Layout, type PageId } from "./components/Layout";
import { SearchPanel } from "./components/SearchPanel";
import { TailorPanel } from "./components/TailorPanel";
import { UploadPanel } from "./components/UploadPanel";
import type { TailorBulletsResponse } from "./types/tailor";

const pages: PageId[] = ["dashboard", "upload", "tailor", "latex", "search"];

const workflowItems = [
  {
    title: "Upload evidence",
    detail: "Index resumes, project notes, and work docs.",
    href: "#/upload",
    icon: FileText,
  },
  {
    title: "Tailor bullets",
    detail: "Generate source-backed bullets from a pasted JD.",
    href: "#/tailor",
    icon: Sparkles,
  },
  {
    title: "Edit LaTeX",
    detail: "Apply accepted bullets into your resume source.",
    href: "#/latex",
    icon: FileCheck2,
  },
  {
    title: "Search context",
    detail: "Inspect the chunks that retrieval is using.",
    href: "#/search",
    icon: Search,
  },
];

function App() {
  const [activePage, setActivePage] = useState<PageId>(() => getPageFromHash());
  const [documentsRefreshKey, setDocumentsRefreshKey] = useState(0);
  const [latestTailorResponse, setLatestTailorResponse] = useState<TailorBulletsResponse | null>(null);

  useEffect(() => {
    function handleHashChange() {
      setActivePage(getPageFromHash());
      window.scrollTo({ top: 0, behavior: "auto" });
    }

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  return (
    <Layout activePage={activePage}>
      {activePage === "dashboard" ? <DashboardPage /> : null}

      {activePage === "upload" ? (
        <PageFrame
          eyebrow="Evidence intake"
          title="Upload Experience"
          description="Add local documents that ResumeRAG can convert, chunk, embed, and retrieve from."
        >
          <div className="grid gap-5 lg:grid-cols-[1fr_1fr]">
            <UploadPanel onUploaded={() => setDocumentsRefreshKey((key) => key + 1)} />
            <DocumentList refreshKey={documentsRefreshKey} />
          </div>
        </PageFrame>
      ) : null}

      {activePage === "tailor" ? (
        <PageFrame
          eyebrow="Generation"
          title="Tailor Bullets"
          description="Paste a job description and generate draft or strict-mode resume bullets from indexed evidence."
        >
          <TailorPanel documentsRefreshKey={documentsRefreshKey} onGenerated={setLatestTailorResponse} />
        </PageFrame>
      ) : null}

      {activePage === "latex" ? (
        <PageFrame
          eyebrow="Resume assembly"
          title="LaTeX Resume Editor"
          description="Paste your resume source and apply generated bullet suggestions into the right section."
        >
          <LatexResumeEditor bullets={latestTailorResponse?.bullets ?? []} skills={latestTailorResponse?.skill_suggestions ?? []} />
        </PageFrame>
      ) : null}

      {activePage === "search" ? (
        <PageFrame
          eyebrow="Retrieval lab"
          title="Search Experience Context"
          description="Probe the vector database directly to understand which chunks are available as evidence."
        >
          <SearchPanel />
        </PageFrame>
      ) : null}
    </Layout>
  );
}

function DashboardPage() {
  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section className="section-shell section-padding">
        <div className="mb-6 flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
          <div className="section-heading">
            <div className="icon-tile border-emerald-200 bg-emerald-50 text-emerald-700">
              <ShieldCheck aria-hidden="true" size={24} />
            </div>
            <div>
              <p className="eyebrow">Privacy-first resume tailoring</p>
              <h1 className="mt-1 text-3xl font-bold tracking-normal text-zinc-950">ResumeRAG</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
                Build tailored resume bullets from your local evidence, then move them into your resume with reviewable edits.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
              <LockKeyhole aria-hidden="true" size={14} />
              Local-first
            </span>
            <span className="inline-flex items-center gap-2 rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs font-semibold text-sky-800">
              <FileCheck2 aria-hidden="true" size={14} />
              Evidence checked
            </span>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {workflowItems.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.title}
                className="subtle-card group flex min-h-28 items-start justify-between gap-4 p-4 transition hover:border-zinc-300 hover:bg-white hover:shadow-sm"
                href={item.href}
              >
                <div className="flex min-w-0 gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-white text-zinc-700 ring-1 ring-zinc-200">
                    <Icon aria-hidden="true" size={18} />
                  </span>
                  <div>
                    <h2 className="text-sm font-semibold text-zinc-950">{item.title}</h2>
                    <p className="mt-1 text-xs leading-5 text-zinc-500">{item.detail}</p>
                  </div>
                </div>
                <ArrowRight aria-hidden="true" className="mt-1 shrink-0 text-zinc-400 transition group-hover:text-zinc-900" size={17} />
              </a>
            );
          })}
        </div>
      </section>

      <HealthChecklist />

      <section className="section-shell section-padding lg:col-span-2">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="eyebrow">Local stack</p>
            <h2 className="text-lg font-semibold text-zinc-950">Runtime Baseline</h2>
            <p className="mt-1 text-sm text-zinc-600">The app is split into focused pages, backed by the same local services.</p>
          </div>
          <span className="inline-flex w-fit items-center gap-2 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs font-semibold text-zinc-700">
            <UploadCloud aria-hidden="true" size={14} />
            Docker Compose
          </span>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          {["React + Vite", "FastAPI", "Postgres + pgvector", "Ollama"].map((label) => (
            <div key={label} className="rounded-md border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold text-zinc-800">
              {label}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

type PageFrameProps = {
  children: ReactNode;
  description: string;
  eyebrow: string;
  title: string;
};

function PageFrame({ children, description, eyebrow, title }: PageFrameProps) {
  return (
    <div className="grid gap-5">
      <section className="section-shell section-padding">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-1 text-2xl font-bold tracking-normal text-zinc-950">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-600">{description}</p>
      </section>
      {children}
    </div>
  );
}

function getPageFromHash(): PageId {
  const normalized = window.location.hash.replace(/^#\/?/, "");
  return pages.includes(normalized as PageId) ? (normalized as PageId) : "dashboard";
}

export default App;
