import { CheckCircle2, CircleDashed, RefreshCw, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { getHealth } from "../api/health";

type BackendState = "checking" | "ok" | "error";

const placeholderChecks = [
  { label: "Database", status: "Migration target" },
  { label: "pgvector", status: "Extension baseline" },
  { label: "Embedding model", status: "Later phase" },
  { label: "Ollama", status: "Later phase" },
];

export function HealthChecklist() {
  const [backendState, setBackendState] = useState<BackendState>("checking");

  async function refresh(signal?: AbortSignal) {
    setBackendState("checking");

    try {
      const health = await getHealth(signal);
      setBackendState(health.backend && health.status === "ok" ? "ok" : "error");
    } catch {
      if (!signal?.aborted) {
        setBackendState("error");
      }
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    refresh(controller.signal);

    return () => controller.abort();
  }, []);

  const BackendIcon = backendState === "ok" ? CheckCircle2 : backendState === "error" ? XCircle : CircleDashed;

  return (
    <aside className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Health</h2>
          <p className="mt-1 text-sm text-zinc-600">Local service status</p>
        </div>
        <button
          type="button"
          aria-label="Refresh health"
          title="Refresh health"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-zinc-200 bg-white text-zinc-700 transition hover:border-zinc-300 hover:bg-zinc-50"
          onClick={() => refresh()}
        >
          <RefreshCw aria-hidden="true" size={16} />
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3">
          <div className="flex items-center gap-3">
            <BackendIcon
              aria-hidden="true"
              className={
                backendState === "ok" ? "text-emerald-600" : backendState === "error" ? "text-red-600" : "text-amber-600"
              }
              size={18}
            />
            <span className="text-sm font-medium text-zinc-900">Backend</span>
          </div>
          <span className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            {backendState === "ok" ? "Connected" : backendState === "error" ? "Offline" : "Checking"}
          </span>
        </div>

        {placeholderChecks.map((check) => (
          <div key={check.label} className="flex items-center justify-between gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3">
            <div className="flex items-center gap-3">
              <CircleDashed aria-hidden="true" className="text-sky-700" size={18} />
              <span className="text-sm font-medium text-zinc-900">{check.label}</span>
            </div>
            <span className="text-xs font-medium uppercase tracking-wide text-zinc-500">{check.status}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
