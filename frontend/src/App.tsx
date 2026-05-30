import { Database, FileText, Search, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";

import { DocumentList } from "./components/DocumentList";
import { HealthChecklist } from "./components/HealthChecklist";
import { Layout } from "./components/Layout";
import { UploadPanel } from "./components/UploadPanel";

const workflowItems = [
  {
    title: "Experience Library",
    status: "Phase 2",
    icon: FileText,
  },
  {
    title: "Vector Search",
    status: "Phase 3",
    icon: Search,
  },
  {
    title: "Tailored Bullets",
    status: "Phase 5",
    icon: Sparkles,
  },
];

function App() {
  const [documentsRefreshKey, setDocumentsRefreshKey] = useState(0);

  return (
    <Layout>
      <section className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-emerald-100 text-emerald-700">
              <ShieldCheck aria-hidden="true" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-zinc-950">ResumeRAG</h1>
              <p className="mt-1 text-sm text-zinc-600">Local-first resume tailoring workspace</p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {workflowItems.map((item) => {
              const Icon = item.icon;

              return (
                <div key={item.title} className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <Icon aria-hidden="true" className="text-zinc-700" size={20} />
                    <span className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-600">
                      {item.status}
                    </span>
                  </div>
                  <h2 className="text-sm font-semibold text-zinc-950">{item.title}</h2>
                </div>
              );
            })}
          </div>
        </div>

        <HealthChecklist />
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-[1fr_1fr]">
        <UploadPanel onUploaded={() => setDocumentsRefreshKey((key) => key + 1)} />
        <DocumentList refreshKey={documentsRefreshKey} />
      </section>

      <section className="mt-5 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <Database aria-hidden="true" className="text-sky-700" size={22} />
          <div>
            <h2 className="text-lg font-semibold text-zinc-950">Stack Baseline</h2>
            <p className="mt-1 text-sm text-zinc-600">Frontend, backend, database, and migration foundation</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          {["React + Vite", "FastAPI", "Postgres + pgvector", "Alembic"].map((label) => (
            <div key={label} className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium text-zinc-800">
              {label}
            </div>
          ))}
        </div>
      </section>
    </Layout>
  );
}

export default App;
