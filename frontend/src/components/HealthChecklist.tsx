import { CheckCircle2, CircleDashed, RefreshCw, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { getFullHealth } from "../api/health";
import type { ComponentHealth, FullHealthResponse } from "../types/health";

type HealthState = "checking" | "ready" | "error";

export function HealthChecklist() {
  const [healthState, setHealthState] = useState<HealthState>("checking");
  const [health, setHealth] = useState<FullHealthResponse | null>(null);

  async function refresh(signal?: AbortSignal) {
    setHealthState("checking");

    try {
      const fullHealth = await getFullHealth(signal);
      setHealth(fullHealth);
      setHealthState("ready");
    } catch {
      if (!signal?.aborted) {
        setHealth(null);
        setHealthState("error");
      }
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    refresh(controller.signal);

    return () => controller.abort();
  }, []);

  const checks = buildChecks(health);

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
        {healthState === "error" ? (
          <HealthRow label="Backend" status="Offline" state="error" />
        ) : null}

        {healthState === "checking" ? (
          ["Backend", "Database", "pgvector", "Embedding model", "Ollama"].map((label) => (
            <HealthRow key={label} label={label} status="Checking" state="checking" />
          ))
        ) : null}

        {healthState === "ready"
          ? checks.map((check) => (
              <HealthRow
                key={check.label}
                label={check.label}
                status={check.status}
                state={check.ok ? "ok" : "error"}
                message={check.message}
              />
            ))
          : null}
      </div>
    </aside>
  );
}

type HealthRowState = "checking" | "ok" | "error";

type HealthRowProps = {
  label: string;
  status: string;
  state: HealthRowState;
  message?: string | null;
};

function HealthRow({ label, status, state, message }: HealthRowProps) {
  const Icon = state === "ok" ? CheckCircle2 : state === "error" ? XCircle : CircleDashed;
  const color = state === "ok" ? "text-emerald-600" : state === "error" ? "text-red-600" : "text-amber-600";

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <Icon aria-hidden="true" className={color} size={18} />
        <span className="truncate text-sm font-medium text-zinc-900">{label}</span>
      </div>
      <span className="shrink-0 text-xs font-medium uppercase tracking-wide text-zinc-500" title={message ?? status}>
        {status}
      </span>
    </div>
  );
}

function buildChecks(health: FullHealthResponse | null) {
  if (!health) {
    return [];
  }

  return [
    {
      label: "Backend",
      ok: health.backend.ok,
      status: toStatus(health.backend, "Connected"),
      message: health.backend.message,
    },
    {
      label: "Database",
      ok: health.database.ok,
      status: toStatus(health.database, "Connected"),
      message: health.database.message,
    },
    {
      label: "pgvector",
      ok: health.pgvector.ok,
      status: toStatus(health.pgvector, "Ready"),
      message: health.pgvector.message,
    },
    {
      label: "Embedding model",
      ok: health.embedding_model.ok,
      status: health.embedding_model.ok ? `${health.embedding_model.dimension} dim` : "Unavailable",
      message: health.embedding_model.message ?? health.embedding_model.model,
    },
    {
      label: "Ollama",
      ok: health.ollama.ok,
      status: health.ollama.ok ? "Connected" : health.ollama.model_available ? "Error" : "Missing",
      message: health.ollama.message ?? `${health.ollama.base_url} | ${health.ollama.model}`,
    },
  ];
}

function toStatus(component: ComponentHealth, okStatus: string) {
  return component.ok ? okStatus : "Offline";
}
