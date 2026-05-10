"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  BriefcaseBusiness,
  LayoutDashboard,
} from "lucide-react";

const navItems = [
  { label: "总览", href: "/dashboard", icon: LayoutDashboard },
  { label: "岗位", href: "/jobs", icon: BriefcaseBusiness },
];

const workflowItems = ["创建岗位", "上传简历", "修正字段", "筛选流转"];

export function WorkspaceShell({
  title,
  description,
  children,
  actions,
  backHref,
  backLabel,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  backHref?: string;
  backLabel?: string;
}) {
  const pathname = usePathname();

  return (
    <main className="app-shell min-h-screen lg:grid lg:grid-cols-[232px_1fr]">
      <aside className="app-sidebar hidden min-h-screen px-4 py-5 lg:block">
        <Link href="/" className="flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white text-sm font-bold text-slate-900">
            R2
          </div>
          <div>
            <p className="text-sm font-semibold">Resumes2AI</p>
            <p className="text-xs text-slate-400">MVP 工作台</p>
          </div>
        </Link>

        <nav className="mt-8 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`flex h-10 items-center gap-3 rounded-md px-3 text-sm transition ${
                  active ? "bg-white text-slate-950" : "text-slate-300 hover:bg-white/10 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-8 rounded-md border border-white/10 bg-white/5 p-3">
          <p className="text-xs font-semibold text-slate-400">MVP 流程</p>
          <ol className="mt-3 space-y-2 text-xs text-slate-300">
            {workflowItems.map((item, index) => (
              <li key={item} className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/10 text-[11px]">
                  {index + 1}
                </span>
                {item}
              </li>
            ))}
          </ol>
        </div>
      </aside>

      <section className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <header className="mb-6 border-b border-border pb-5">
            {backHref ? (
              <Link href={backHref} className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="h-4 w-4" />
                {backLabel ?? "返回"}
              </Link>
            ) : null}
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <h1 className="text-2xl font-semibold tracking-normal text-foreground">{title}</h1>
                {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p> : null}
              </div>
              {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
            </div>
          </header>

          {children}
        </div>
      </section>
    </main>
  );
}

export function Notice({
  tone,
  children,
  action,
}: {
  tone: "error" | "success" | "info";
  children: ReactNode;
  action?: ReactNode;
}) {
  const className =
    tone === "error"
      ? "border-red-200 bg-red-50 text-red-700"
      : tone === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-sky-200 bg-sky-50 text-sky-800";
  return (
    <div className={`mb-5 flex flex-col gap-3 rounded-md border px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between ${className}`}>
      <div>{children}</div>
      {action}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-md border border-dashed border-border bg-muted/60 px-6 py-10 text-center">
      <p className="text-base font-semibold">{title}</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
