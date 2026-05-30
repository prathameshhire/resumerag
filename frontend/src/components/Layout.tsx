import type { ReactNode } from "react";

type LayoutProps = {
  children: ReactNode;
};

export function Layout({ children }: LayoutProps) {
  const navItems = [
    { label: "Dashboard", href: "#dashboard" },
    { label: "Upload", href: "#upload" },
    { label: "Tailor", href: "#tailor" },
    { label: "Search", href: "#search" },
  ];

  return (
    <div className="min-h-screen bg-zinc-100 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="text-sm font-semibold text-zinc-950">ResumeRAG</div>
          <nav aria-label="Primary" className="flex items-center gap-2 text-sm">
            {navItems.map((item, index) => (
              <a
                key={item.href}
                href={item.href}
                className={
                  index === 0
                    ? "rounded-md bg-zinc-900 px-3 py-2 font-medium text-white"
                    : "rounded-md px-3 py-2 font-medium text-zinc-500"
                }
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
