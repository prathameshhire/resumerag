import type { ReactNode } from "react";
import { Database, FileCode2, FileUp, HeartPulse, Search, Sparkles } from "lucide-react";

export type PageId = "dashboard" | "upload" | "tailor" | "latex" | "search";

type LayoutProps = {
  activePage: PageId;
  children: ReactNode;
};

export function Layout({ activePage, children }: LayoutProps) {
  const navItems = [
    { id: "dashboard" as const, label: "Status", href: "#/dashboard", icon: HeartPulse },
    { id: "upload" as const, label: "Upload", href: "#/upload", icon: FileUp },
    { id: "tailor" as const, label: "Tailor", href: "#/tailor", icon: Sparkles },
    { id: "latex" as const, label: "LaTeX", href: "#/latex", icon: FileCode2 },
    { id: "search" as const, label: "Search", href: "#/search", icon: Search },
  ];

  return (
    <div className="skeuo-app min-h-screen text-zinc-950">
      <header className="skeuo-header sticky top-0 z-20">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <div className="skeuo-brand-token flex h-10 w-10 items-center justify-center rounded-md text-white">
              <Database aria-hidden="true" size={19} />
            </div>
            <div>
              <div className="text-sm font-bold text-zinc-950">ResumeRAG</div>
              <div className="text-xs font-medium text-zinc-500">Local evidence workspace</div>
            </div>
          </div>
          <nav aria-label="Primary" className="skeuo-nav flex w-full flex-wrap items-center gap-1 rounded-lg p-1 text-sm lg:w-auto">
            {navItems.map((item) => {
              const Icon = item.icon;

              return (
              <a
                key={item.href}
                href={item.href}
                aria-current={activePage === item.id ? "page" : undefined}
                className={`inline-flex shrink-0 items-center gap-2 rounded-md px-3 py-2 font-semibold transition ${
                  activePage === item.id
                    ? "text-zinc-950"
                    : "text-zinc-600 hover:bg-white hover:text-zinc-950"
                }`}
              >
                <Icon aria-hidden="true" size={15} />
                {item.label}
              </a>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
