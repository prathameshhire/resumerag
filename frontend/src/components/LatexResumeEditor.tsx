import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clipboard,
  Download,
  FileCode2,
  GitPullRequestArrow,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Replace,
  X,
} from "lucide-react";
import { useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";

import { exportLatexPdf } from "../api/latex";
import type { TailoredBullet, TailoredSkill } from "../types/tailor";
import {
  addLatexSkill,
  findClosestLatexItem,
  findBestLatexEntry,
  findBestLatexSkillGroup,
  findFallbackLatexEntry,
  findLeastRelevantLatexSkill,
  insertResumeItem,
  parseLatexResume,
  replaceLatexSkill,
  replaceResumeItem,
  skillExistsInGroup,
  type LatexResumeEntry,
  type LatexResumeItem,
  type LatexSkillGroup,
  type LatexSkillValue,
  type ParsedLatexResume,
} from "../utils/latexResume";

type LatexResumeEditorProps = {
  bullets: TailoredBullet[];
  skills: TailoredSkill[];
};

type PatchStatus = "pending" | "accepted" | "rejected";
type ViewMode = "split" | "code" | "preview";

const LATEX_STORAGE_KEY = "resumerag:latex-source";
const LATEX_STORAGE_SAVED_AT_KEY = "resumerag:latex-source-saved-at";

export function LatexResumeEditor({ bullets, skills }: LatexResumeEditorProps) {
  const [latex, setLatex] = useState(() => loadStoredLatex());
  const [previewLatex, setPreviewLatex] = useState(() => loadStoredLatex());
  const [lastPreviewAt, setLastPreviewAt] = useState<Date | null>(null);
  const [patchStatuses, setPatchStatuses] = useState<Record<string, PatchStatus>>({});
  const [copied, setCopied] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<Date | null>(() => loadStoredLatexSavedAt());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [editorWidth, setEditorWidth] = useState(50);
  const [previewZoom, setPreviewZoom] = useState(82);
  const [fontSize, setFontSize] = useState(13);
  const [previewFirst, setPreviewFirst] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("split");
  const workspaceRef = useRef<HTMLDivElement | null>(null);

  const parsed = useMemo(() => parseLatexResume(latex), [latex]);
  const previewParsed = useMemo(() => parseLatexResume(previewLatex), [previewLatex]);
  const lineNumbers = useMemo(() => latex.split("\n").map((_, index) => index + 1).join("\n"), [latex]);
  const patches = useMemo(
    () =>
      bullets.map((bullet, index) => {
        const id = `${index}:${bullet.bullet}`;
        const confidentTarget = findBestLatexEntry(parsed, bullet);
        const target = confidentTarget ?? findFallbackLatexEntry(parsed, bullet);
        return {
          bullet,
          closestItem: target ? findClosestLatexItem(target, bullet.bullet) : undefined,
          id,
          status: patchStatuses[id] ?? "pending",
          target,
          targetIsFallback: !confidentTarget && Boolean(target),
        };
      }),
    [bullets, parsed, patchStatuses],
  );
  const skillPatches = useMemo(
    () =>
      skills.map((skill, index) => {
        const id = `skill:${index}:${skill.skill}:${skill.category}`;
        const target = findBestLatexSkillGroup(parsed, skill);
        const protectedSkillNames = skills.map((suggestion) => suggestion.skill);
        return {
          alreadyPresent: target ? skillExistsInGroup(target, skill.skill) : false,
          id,
          replaceTarget: target ? findLeastRelevantLatexSkill(target, protectedSkillNames) : undefined,
          skill,
          status: patchStatuses[id] ?? "pending",
          target,
        };
      }),
    [skills, parsed, patchStatuses],
  );

  function applyPatch(id: string, bullet: TailoredBullet) {
    const target = findBestLatexEntry(parsed, bullet) ?? findFallbackLatexEntry(parsed, bullet);
    if (!target) {
      return;
    }

    commitLatex(insertResumeItem(latex, target, bullet.bullet));
    setPatchStatuses((current) => ({ ...current, [id]: "accepted" }));
  }

  function replacePatch(id: string, bullet: TailoredBullet) {
    const target = findBestLatexEntry(parsed, bullet);
    const closestItem = target ? findClosestLatexItem(target, bullet.bullet) : undefined;
    if (!target || !closestItem) {
      return;
    }

    commitLatex(replaceResumeItem(latex, closestItem, bullet.bullet));
    setPatchStatuses((current) => ({ ...current, [id]: "accepted" }));
  }

  function rejectPatch(id: string) {
    setPatchStatuses((current) => ({ ...current, [id]: "rejected" }));
  }

  function applySkillPatch(id: string, skill: TailoredSkill) {
    const target = findBestLatexSkillGroup(parsed, skill);
    if (!target || skillExistsInGroup(target, skill.skill)) {
      return;
    }

    commitLatex(addLatexSkill(latex, target, skill.skill));
    setPatchStatuses((current) => ({ ...current, [id]: "accepted" }));
  }

  function replaceSkillPatch(id: string, skill: TailoredSkill) {
    const target = findBestLatexSkillGroup(parsed, skill);
    const protectedSkillNames = skills.map((suggestion) => suggestion.skill);
    const replaceTarget = target ? findLeastRelevantLatexSkill(target, protectedSkillNames) : undefined;
    if (!target || !replaceTarget || skillExistsInGroup(target, skill.skill)) {
      return;
    }

    commitLatex(replaceLatexSkill(latex, replaceTarget, skill.skill));
    setPatchStatuses((current) => ({ ...current, [id]: "accepted" }));
  }

  function handleLatexChange(value: string) {
    commitLatex(value);
  }

  function commitLatex(value: string) {
    setLatex(value);
    setSavedAt(saveStoredLatex(value));
    updatePreview(value);
  }

  function startNewLatex() {
    if (latex.trim() && !window.confirm("Clear the saved resume source and paste a new .tex file?")) {
      return;
    }

    commitLatex("");
    setPatchStatuses({});
    setViewMode("code");
  }

  function updatePreview(value: string) {
    setPreviewLatex(value);
    setLastPreviewAt(new Date());
  }

  async function copyLatex() {
    try {
      await navigator.clipboard.writeText(latex);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  function downloadLatex() {
    const blob = new Blob([latex], { type: "text/x-tex" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "resume-updated.tex";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function downloadPdf() {
    if (!latex.trim()) {
      return;
    }

    setPdfError(null);
    setIsExportingPdf(true);
    try {
      const pdfBlob = await exportLatexPdf(latex, "resume-updated.pdf");
      const url = URL.createObjectURL(pdfBlob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "resume-updated.pdf";
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (error) {
      setPdfError(error instanceof Error ? error.message : "PDF export failed.");
    } finally {
      setIsExportingPdf(false);
    }
  }

  const pendingCount = [...patches, ...skillPatches].filter((patch) => patch.status === "pending").length;
  const acceptedCount = [...patches, ...skillPatches].filter((patch) => patch.status === "accepted").length;
  const isSplitView = viewMode === "split";
  const contentColumns = isSplitView
    ? `minmax(380px, ${previewFirst ? 100 - editorWidth : editorWidth}fr) 12px minmax(380px, ${previewFirst ? editorWidth : 100 - editorWidth}fr)`
    : "minmax(520px, 1fr)";
  const workspaceColumns = sidebarOpen ? `250px ${contentColumns}` : contentColumns;

  function startPaneResize(event: ReactPointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    const bounds = workspaceRef.current?.getBoundingClientRect();
    if (!bounds) {
      return;
    }

    const sidebarWidth = sidebarOpen ? 250 : 0;
    const contentLeft = bounds.left + sidebarWidth;
    const contentWidth = Math.max(bounds.width - sidebarWidth, 1);

    function handlePointerMove(moveEvent: PointerEvent) {
      const rawPosition = ((moveEvent.clientX - contentLeft) / contentWidth) * 100;
      const nextEditorWidth = previewFirst ? 100 - rawPosition : rawPosition;
      setEditorWidth(Math.min(70, Math.max(35, Math.round(nextEditorWidth))));
    }

    function stopResize() {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopResize);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopResize);
  }

  return (
    <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm shadow-zinc-200/60">
      <div className="flex min-h-12 flex-wrap items-center justify-between gap-3 border-b border-zinc-200 bg-white px-4 py-2 text-zinc-950">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-emerald-200 bg-emerald-50 text-emerald-700">
            <FileCode2 aria-hidden="true" size={17} />
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">Resume LaTeX Workspace</div>
            <div className="text-xs text-zinc-500">
              {savedAt ? `main.tex - saved locally ${savedAt.toLocaleTimeString()}` : "main.tex - paste a resume source to save locally"}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex min-h-8 overflow-hidden rounded-md border border-zinc-300 bg-white p-0.5" aria-label="LaTeX workspace view">
            <button type="button" className={viewModeButtonClassName(viewMode === "split")} onClick={() => setViewMode("split")}>
              Split
            </button>
            <button type="button" className={viewModeButtonClassName(viewMode === "code")} onClick={() => setViewMode("code")}>
              Code
            </button>
            <button type="button" className={viewModeButtonClassName(viewMode === "preview")} onClick={() => setViewMode("preview")}>
              Preview
            </button>
          </div>
          <button type="button" className="editor-toolbar-button" onClick={() => setSidebarOpen((open) => !open)}>
            {sidebarOpen ? <PanelLeftClose aria-hidden="true" size={15} /> : <PanelLeftOpen aria-hidden="true" size={15} />}
            {sidebarOpen ? "Hide outline" : "Show outline"}
          </button>
          <button type="button" className="editor-toolbar-button" onClick={() => setPreviewFirst((value) => !value)} disabled={!isSplitView}>
            <Replace aria-hidden="true" size={15} />
            Swap panes
          </button>
          <button type="button" className="editor-toolbar-button" onClick={startNewLatex}>
            <FileCode2 aria-hidden="true" size={15} />
            Paste new .tex
          </button>
          <button type="button" className="editor-toolbar-button" onClick={() => updatePreview(latex)} disabled={!latex.trim()}>
            <RefreshCw aria-hidden="true" size={15} />
            Refresh Preview
          </button>
          <button type="button" className="editor-toolbar-button" onClick={copyLatex} disabled={!latex.trim()}>
            {copied ? <CheckCircle2 aria-hidden="true" size={15} /> : <Clipboard aria-hidden="true" size={15} />}
            {copied ? "Copied" : "Copy"}
          </button>
          <button type="button" className="editor-toolbar-button" onClick={downloadLatex} disabled={!latex.trim()}>
            <Download aria-hidden="true" size={15} />
            Download .tex
          </button>
          <button type="button" className="editor-toolbar-button" onClick={downloadPdf} disabled={!latex.trim() || isExportingPdf}>
            <Download aria-hidden="true" className={isExportingPdf ? "animate-spin" : undefined} size={15} />
            {isExportingPdf ? "Compiling PDF" : "Export PDF"}
          </button>
        </div>
      </div>

      {pdfError ? <div className="status-note mx-4 mt-3 border-red-200 bg-red-50 text-red-900">{pdfError}</div> : null}

      <div className="flex flex-wrap items-center gap-4 border-b border-zinc-200 bg-zinc-50 px-4 py-2 text-xs text-zinc-700">
        {isSplitView ? (
          <label className="flex items-center gap-2">
            Editor width
            <ChevronLeft aria-hidden="true" size={13} />
            <input
              aria-label="Editor width"
              className="w-28 accent-zinc-900"
              max={70}
              min={35}
              type="range"
              value={editorWidth}
              onChange={(event) => setEditorWidth(Number(event.target.value))}
            />
            <ChevronRight aria-hidden="true" size={13} />
          </label>
        ) : null}
        {viewMode !== "code" ? (
          <label className="flex items-center gap-2">
            Preview zoom
            <input
              aria-label="Preview zoom"
              className="w-28 accent-zinc-900"
              max={110}
              min={60}
              type="range"
              value={previewZoom}
              onChange={(event) => setPreviewZoom(Number(event.target.value))}
            />
            <span>{previewZoom}%</span>
          </label>
        ) : null}
        {viewMode !== "preview" ? (
          <label className="flex items-center gap-2">
            Font
            <input
              aria-label="Editor font size"
              className="w-24 accent-zinc-900"
              max={16}
              min={11}
              type="range"
              value={fontSize}
              onChange={(event) => setFontSize(Number(event.target.value))}
            />
            <span>{fontSize}px</span>
          </label>
        ) : null}
        <span className="ml-auto text-zinc-500">
          {lastPreviewAt ? `Preview refreshed ${lastPreviewAt.toLocaleTimeString()}` : "Preview updates as you edit"}
        </span>
      </div>

      <div className="overflow-x-auto">
        <div ref={workspaceRef} className="grid h-[720px] items-stretch" style={{ gridTemplateColumns: workspaceColumns }}>
          {sidebarOpen ? (
            <EditorSidebar
              acceptedCount={acceptedCount}
              parsed={parsed}
              pendingCount={pendingCount}
              patches={patches}
              skillPatches={skillPatches}
              onApply={applyPatch}
              onApplySkill={applySkillPatch}
              onReject={rejectPatch}
              onReplace={replacePatch}
              onReplaceSkill={replaceSkillPatch}
            />
          ) : null}

          {viewMode === "split" ? (
            <>
              {previewFirst ? (
                <PreviewPane parsed={previewParsed} zoom={previewZoom} />
              ) : (
                <CodePane fontSize={fontSize} latex={latex} lineNumbers={lineNumbers} onChange={handleLatexChange} />
              )}

              <button
                type="button"
                aria-label="Drag to resize code and preview panes"
                className="group flex cursor-col-resize touch-none select-none items-center justify-center border-x border-zinc-200 bg-zinc-100 transition hover:bg-zinc-200"
                onDoubleClick={() => setPreviewFirst((value) => !value)}
                onPointerDown={startPaneResize}
                title="Drag to resize. Double-click to swap panes."
              >
                <span className="flex h-12 w-7 flex-col items-center justify-center rounded-full border border-zinc-300 bg-white text-zinc-600 shadow-sm group-hover:text-zinc-950">
                  <ChevronRight aria-hidden="true" size={15} />
                  <ChevronLeft aria-hidden="true" size={15} />
                </span>
              </button>

              {previewFirst ? (
                <CodePane fontSize={fontSize} latex={latex} lineNumbers={lineNumbers} onChange={handleLatexChange} />
              ) : (
                <PreviewPane parsed={previewParsed} zoom={previewZoom} />
              )}
            </>
          ) : viewMode === "code" ? (
            <CodePane fontSize={fontSize} latex={latex} lineNumbers={lineNumbers} onChange={handleLatexChange} />
          ) : (
            <PreviewPane parsed={previewParsed} zoom={previewZoom} />
          )}
        </div>
      </div>
    </section>
  );
}

type CodePaneProps = {
  fontSize: number;
  latex: string;
  lineNumbers: string;
  onChange: (value: string) => void;
};

function CodePane({ fontSize, latex, lineNumbers, onChange }: CodePaneProps) {
  return (
    <div className="flex h-[720px] min-w-0 flex-col border-r border-zinc-200 bg-white">
            <div className="flex h-10 shrink-0 items-center justify-between border-b border-zinc-200 bg-zinc-50 px-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-700">
                <FileCode2 aria-hidden="true" size={15} />
                main.tex
              </div>
              <span className="rounded-md bg-white px-2 py-1 text-xs font-medium text-zinc-500 ring-1 ring-zinc-200">Editing</span>
            </div>
            <div className="flex min-h-0 min-w-0 flex-1 overflow-hidden bg-white">
              <pre
                aria-hidden="true"
                className="select-none overflow-hidden border-r border-zinc-200 bg-zinc-50 px-3 py-3 text-right font-mono leading-6 text-zinc-400"
                style={{ fontSize }}
              >
                {lineNumbers || "1"}
              </pre>
              <textarea
                className="min-h-full flex-1 resize-none border-0 bg-white px-3 py-3 font-mono leading-6 text-zinc-950 outline-none"
                placeholder="Paste your resume .tex here"
                spellCheck={false}
                style={{ fontSize }}
                value={latex}
                onChange={(event) => onChange(event.target.value)}
              />
            </div>
    </div>
  );
}

function PreviewPane({ parsed, zoom }: { parsed: ParsedLatexResume; zoom: number }) {
  return (
    <div className="flex h-[720px] min-w-0 flex-col bg-zinc-100">
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-zinc-200 bg-white px-3 text-zinc-950">
        <div className="text-sm font-semibold">Preview</div>
        <span className="rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-500">1 / 1</span>
      </div>
      <ResumePreview parsed={parsed} zoom={zoom} />
    </div>
  );
}

type Patch = {
  bullet: TailoredBullet;
  closestItem?: LatexResumeItem;
  id: string;
  status: PatchStatus;
  target?: LatexResumeEntry;
  targetIsFallback: boolean;
};

type SkillPatch = {
  alreadyPresent: boolean;
  id: string;
  replaceTarget?: LatexSkillValue;
  skill: TailoredSkill;
  status: PatchStatus;
  target?: LatexSkillGroup;
};

type EditorSidebarProps = {
  acceptedCount: number;
  parsed: ParsedLatexResume;
  patches: Patch[];
  pendingCount: number;
  skillPatches: SkillPatch[];
  onApply: (id: string, bullet: TailoredBullet) => void;
  onApplySkill: (id: string, skill: TailoredSkill) => void;
  onReject: (id: string) => void;
  onReplace: (id: string, bullet: TailoredBullet) => void;
  onReplaceSkill: (id: string, skill: TailoredSkill) => void;
};

function EditorSidebar({
  acceptedCount,
  parsed,
  patches,
  pendingCount,
  skillPatches,
  onApply,
  onApplySkill,
  onReject,
  onReplace,
  onReplaceSkill,
}: EditorSidebarProps) {
  const hasPatchSuggestions = patches.length > 0 || skillPatches.length > 0;

  return (
    <aside className="grid h-[720px] min-w-0 grid-rows-[auto_minmax(0,1fr)_minmax(0,1.2fr)] overflow-hidden border-r border-zinc-200 bg-zinc-50 text-zinc-950">
      <div className="border-b border-zinc-200 p-3">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">File tree</div>
        <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-800">
          <FileCode2 aria-hidden="true" size={15} />
          main.tex
        </div>
      </div>

      <div className="min-h-0 overflow-y-auto border-b border-zinc-200 p-3">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">File outline</div>
        {parsed.sections.length > 0 ? (
          <div className="space-y-2">
            {parsed.sections.map((section) => (
              <div key={section.title}>
                <div className="text-sm font-semibold text-zinc-900">{section.title}</div>
                <div className="mt-1 space-y-1 pl-3 text-xs text-zinc-500">
                  {section.entries.map((entry) => (
                    <div key={entry.id} className="truncate">{entry.title}</div>
                  ))}
                  {section.skills?.map((skill) => (
                    <div key={skill.label} className="truncate">{skill.label}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs leading-5 text-zinc-500">Paste resume source to populate the outline.</p>
        )}
      </div>

      <div className="min-h-0 overflow-y-auto p-3">
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Patch queue</div>
          <div className="text-[11px] text-zinc-500">{pendingCount} pending / {acceptedCount} accepted</div>
        </div>
        {!hasPatchSuggestions ? (
          <p className="text-xs leading-5 text-zinc-500">Generate bullets and skill suggestions on the Tailor page to create patch suggestions.</p>
        ) : (
          <div className="space-y-2">
            {patches.length > 0 && !parsed.hasResumeMacros ? (
              <p className="rounded-md border border-amber-200 bg-amber-50 px-2 py-2 text-xs leading-5 text-amber-900">
                Paste a resume source with supported resume macros before applying bullet patches.
              </p>
            ) : null}

            {patches.map((patch, index) => (
              parsed.hasResumeMacros ? (
                <PatchCard
                  bullet={patch.bullet}
                  closestItem={patch.closestItem}
                  index={index}
                  key={patch.id}
                  onApply={() => onApply(patch.id, patch.bullet)}
                  onReject={() => onReject(patch.id)}
                  onReplace={() => onReplace(patch.id, patch.bullet)}
                  status={patch.status}
                  target={patch.target}
                  targetIsFallback={patch.targetIsFallback}
                />
              ) : null
            ))}

            {skillPatches.length > 0 ? (
              <div className="pt-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">Technical skills</div>
            ) : null}
            {skillPatches.map((patch, index) => (
              <SkillPatchCard
                alreadyPresent={patch.alreadyPresent}
                index={index}
                key={patch.id}
                onApply={() => onApplySkill(patch.id, patch.skill)}
                onReject={() => onReject(patch.id)}
                onReplace={() => onReplaceSkill(patch.id, patch.skill)}
                replaceTarget={patch.replaceTarget}
                skill={patch.skill}
                status={patch.status}
                target={patch.target}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

type PatchCardProps = {
  bullet: TailoredBullet;
  closestItem?: LatexResumeItem;
  index: number;
  onApply: () => void;
  onReject: () => void;
  onReplace: () => void;
  status: PatchStatus;
  target?: LatexResumeEntry;
  targetIsFallback: boolean;
};

function PatchCard({ bullet, closestItem, index, onApply, onReject, onReplace, status, target, targetIsFallback }: PatchCardProps) {
  const addDisabled = status !== "pending" || !target;
  const replaceDisabled = status !== "pending" || !target || !closestItem || targetIsFallback;

  return (
    <article className="rounded-md border border-zinc-200 bg-white p-3 shadow-sm shadow-zinc-200/50">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-zinc-950 text-xs font-semibold text-white">{index + 1}</span>
          <span className={statusClassName(status)}>{status}</span>
        </div>
        <GitPullRequestArrow aria-hidden="true" className="text-zinc-400" size={16} />
      </div>
      <p className="line-clamp-4 text-xs leading-5 text-zinc-800">{bullet.bullet}</p>
      <div className="mt-2 rounded border border-violet-200 bg-violet-50 px-2 py-1 text-[11px] leading-4 text-violet-900">
        {target
          ? `${targetIsFallback ? "Fallback target" : "Target"}: ${target.section} - ${target.title}${target.organization ? ` / ${target.organization}` : ""}`
          : "No add target found"}
      </div>
      <div className="mt-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-1 text-[11px] leading-4 text-zinc-700">
        <div className="font-semibold text-zinc-900">Closest existing bullet</div>
        <p className="mt-1 line-clamp-3">{closestItem?.text ?? "No close bullet match found."}</p>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <button type="button" className="editor-small-button" onClick={onApply} disabled={addDisabled}>
          <CheckCircle2 aria-hidden="true" size={13} />
          Add
        </button>
        <button type="button" className="editor-small-button" onClick={onReplace} disabled={replaceDisabled}>
          <Replace aria-hidden="true" size={13} />
          Replace
        </button>
        <button type="button" className="editor-small-button col-span-2" onClick={onReject} disabled={status !== "pending"}>
          <X aria-hidden="true" size={13} />
          Reject
        </button>
      </div>
    </article>
  );
}

type SkillPatchCardProps = {
  alreadyPresent: boolean;
  index: number;
  onApply: () => void;
  onReject: () => void;
  onReplace: () => void;
  replaceTarget?: LatexSkillValue;
  skill: TailoredSkill;
  status: PatchStatus;
  target?: LatexSkillGroup;
};

function SkillPatchCard({ alreadyPresent, index, onApply, onReject, onReplace, replaceTarget, skill, status, target }: SkillPatchCardProps) {
  const addDisabled = status !== "pending" || !target || alreadyPresent;
  const replaceDisabled = addDisabled || !replaceTarget;

  return (
    <article className="rounded-md border border-emerald-200 bg-emerald-50/70 p-3 shadow-sm shadow-zinc-200/50">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-emerald-900 text-xs font-semibold text-white">S{index + 1}</span>
          <span className={statusClassName(status)}>{alreadyPresent && status === "pending" ? "present" : status}</span>
        </div>
        <GitPullRequestArrow aria-hidden="true" className="text-emerald-700" size={16} />
      </div>
      <p className="text-sm font-semibold text-zinc-950">{skill.skill}</p>
      <div className="mt-2 rounded border border-emerald-200 bg-white px-2 py-1 text-[11px] leading-4 text-emerald-950">
        {target ? `${target.label} row` : `No ${skill.category} row found`}
      </div>
      <div className="mt-2 rounded border border-zinc-200 bg-white/80 px-2 py-1 text-[11px] leading-4 text-zinc-700">
        <div className="font-semibold text-zinc-900">Replace candidate</div>
        <p className="mt-1 line-clamp-2">{replaceTarget?.text ?? "No skill available to replace."}</p>
      </div>
      <div className="mt-2 text-[11px] leading-4 text-zinc-700">
        <span className="font-semibold text-zinc-900">Requirement:</span> {skill.matched_requirement}
      </div>
      {skill.notes ? <div className="mt-1 text-[11px] leading-4 text-zinc-600">{skill.notes}</div> : null}
      <div className="mt-2 grid grid-cols-2 gap-2">
        <button type="button" className="editor-small-button" onClick={onApply} disabled={addDisabled}>
          <CheckCircle2 aria-hidden="true" size={13} />
          Add
        </button>
        <button type="button" className="editor-small-button" onClick={onReplace} disabled={replaceDisabled}>
          <Replace aria-hidden="true" size={13} />
          Replace
        </button>
        <button type="button" className="editor-small-button col-span-2" onClick={onReject} disabled={status !== "pending"}>
          <X aria-hidden="true" size={13} />
          Reject
        </button>
      </div>
    </article>
  );
}

function ResumePreview({ parsed, zoom }: { parsed: ParsedLatexResume; zoom: number }) {
  if (!parsed.hasResumeMacros) {
    return (
      <div className="flex h-[680px] flex-1 items-center justify-center p-6">
        <div className="rounded-lg border border-dashed border-zinc-300 bg-white px-4 py-8 text-center text-sm leading-6 text-zinc-500">
          Paste resume LaTeX to render a structured preview.
        </div>
      </div>
    );
  }

  const scale = zoom / 100;

  return (
    <div className="h-[680px] flex-1 overflow-auto bg-zinc-100 p-6">
      <div
        className="mx-auto min-h-[900px] max-w-[820px] bg-white px-10 py-8 font-serif text-zinc-950 shadow-xl"
        style={{
          transform: `scale(${scale})`,
          transformOrigin: "top center",
          width: `${100 / scale}%`,
        }}
      >
        <div className="mb-5 text-center">
          <div className="text-2xl font-bold">{parsed.heading.name || "Resume Preview"}</div>
          {parsed.heading.contacts.length > 0 ? (
            <div className="mt-1 flex flex-wrap justify-center gap-x-2 gap-y-1 text-xs text-zinc-700">
              {parsed.heading.contacts.map((contact, index) => (
                <span key={`${contact}-${index}`}>
                  {contact}
                  {index < parsed.heading.contacts.length - 1 ? <span className="ml-2 text-zinc-400">|</span> : null}
                </span>
              ))}
            </div>
          ) : (
            <div className="mt-1 text-xs text-zinc-500">Live parsed preview</div>
          )}
        </div>

        {parsed.sections.map((section) => (
          <section key={section.title} className="mb-4">
            <h4 className="mb-2 border-b border-zinc-950 pb-1 text-sm font-semibold uppercase tracking-wide">{section.title}</h4>
            <div className="space-y-3">
              {section.entries.length > 0 ? (
                section.entries.map((entry) => <PreviewEntry entry={entry} key={entry.id} />)
              ) : section.skills && section.skills.length > 0 ? (
                <div className="space-y-1 text-xs leading-5">
                  {section.skills.map((skill) => (
                    <div key={skill.label}>
                      <span className="font-semibold">{skill.label}: </span>
                      <span>{skill.value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-zinc-500">No supported entries detected.</p>
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function PreviewEntry({ entry }: { entry: LatexResumeEntry }) {
  return (
    <article>
      <div className="flex items-start justify-between gap-4 text-sm">
        <div className="font-semibold">{entry.title}</div>
        {entry.date ? <div className="shrink-0 text-xs">{entry.date}</div> : null}
      </div>
      <div className="mt-0.5 flex items-start justify-between gap-4 text-xs italic text-zinc-700">
        <div>{entry.organization ?? entry.detail}</div>
        {entry.location ? <div className="shrink-0">{entry.location}</div> : null}
      </div>
      {entry.items.length > 0 ? (
        <ul className="mt-1 list-disc space-y-0.5 pl-5 text-xs leading-5">
          {entry.items.map((item, index) => (
            <li key={`${item.text}-${index}`}>{item.text}</li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function statusClassName(status: PatchStatus) {
  if (status === "accepted") {
    return "rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-800";
  }
  if (status === "rejected") {
    return "rounded-md border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[11px] font-semibold text-zinc-600";
  }
  return "rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-900";
}

function viewModeButtonClassName(isActive: boolean) {
  return [
    "rounded px-3 py-1 text-xs font-semibold transition",
    isActive ? "bg-zinc-950 text-white shadow-sm" : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950",
  ].join(" ");
}

function loadStoredLatex(): string {
  try {
    return window.localStorage.getItem(LATEX_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function loadStoredLatexSavedAt(): Date | null {
  try {
    const value = window.localStorage.getItem(LATEX_STORAGE_SAVED_AT_KEY);
    if (!value) {
      return null;
    }

    const savedAt = new Date(value);
    return Number.isNaN(savedAt.getTime()) ? null : savedAt;
  } catch {
    return null;
  }
}

function saveStoredLatex(value: string): Date | null {
  try {
    if (!value.trim()) {
      window.localStorage.removeItem(LATEX_STORAGE_KEY);
      window.localStorage.removeItem(LATEX_STORAGE_SAVED_AT_KEY);
      return null;
    }

    const savedAt = new Date();
    window.localStorage.setItem(LATEX_STORAGE_KEY, value);
    window.localStorage.setItem(LATEX_STORAGE_SAVED_AT_KEY, savedAt.toISOString());
    return savedAt;
  } catch {
    return null;
  }
}
