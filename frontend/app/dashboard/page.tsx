"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  Loader2,
  Plus,
  RefreshCw,
  Sparkles,
  Upload,
  Users,
} from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import { DashboardPayload, getDashboard } from "@/lib/api";

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      setDashboard(await getDashboard());
    } catch (err) {
      setError(err instanceof Error ? err.message : "工作台加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const hasWork = useMemo(() => {
    if (!dashboard) return false;
    return dashboard.todos.some((todo) => todo.count > 0) || dashboard.summary.open_jobs > 0;
  }, [dashboard]);

  return (
    <WorkspaceShell
      title="工作台总览"
      description="集中查看开放岗位、待处理候选人、解析与评分异常，把今天最该处理的事项放到前面。"
      actions={
        <>
          <button onClick={() => void loadDashboard()} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新
          </button>
          <Link href="/jobs/new" className="btn-primary">
            <Plus className="h-4 w-4" />
            创建岗位
          </Link>
          <Link href="/resumes/upload" className="btn-secondary">
            <Upload className="h-4 w-4" />
            上传简历
          </Link>
        </>
      }
    >
      {error ? (
        <Notice
          tone="error"
          action={
            <button onClick={() => void loadDashboard()} className="btn-secondary h-8 text-xs">
              重试
            </button>
          }
        >
          {error}
        </Notice>
      ) : null}

      {loading ? (
        <div className="panel flex items-center gap-2 p-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          正在加载工作台
        </div>
      ) : dashboard ? (
        <div className="space-y-5">
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Metric icon={BriefcaseBusiness} label="开放岗位" value={dashboard.summary.open_jobs} />
            <Metric icon={Users} label="候选人总数" value={dashboard.summary.total_candidates} />
            <Metric icon={Sparkles} label="高匹配候选人" value={dashboard.summary.high_match_candidates} />
            <Metric icon={Clock3} label="待沟通候选人" value={dashboard.summary.pending_contact_candidates} />
          </section>

          <section className="grid gap-5 lg:grid-cols-[1fr_380px]">
            <div className="panel overflow-hidden">
              <div className="border-b border-border px-5 py-4">
                <h2 className="text-base font-semibold">今日待处理</h2>
              </div>
              {!hasWork ? (
                <div className="p-5">
                  <EmptyState
                    title="暂无待处理事项"
                    description="创建岗位并上传简历后，这里会展示高匹配候选人、待沟通事项和异常。"
                    action={
                      <Link href="/jobs/new" className="btn-primary">
                        创建岗位
                      </Link>
                    }
                  />
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {dashboard.todos.map((todo) => (
                    <Link
                      key={todo.key}
                      href={todo.href}
                      className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-muted/70"
                    >
                      <span className="flex min-w-0 items-center gap-3">
                        <TodoIcon tone={todo.tone} />
                        <span className="truncate text-sm font-medium">{todo.title}</span>
                      </span>
                      <span className={todo.count > 0 ? "status-pill" : "text-sm text-muted-foreground"}>
                        {todo.count}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <aside className="panel overflow-hidden">
              <div className="border-b border-border px-5 py-4">
                <h2 className="text-base font-semibold">异常概览</h2>
              </div>
              <div className="space-y-3 p-5">
                <AlertRow label="解析失败" value={dashboard.summary.parse_failed_resumes} />
                <AlertRow label="评分失败" value={dashboard.summary.match_failed_tasks} />
                <AlertRow label="重复待复核" value={dashboard.summary.pending_duplicate_reviews} />
                <AlertRow label="待初筛" value={dashboard.summary.pending_candidates} neutral />
                <AlertRow label="今日新增" value={dashboard.summary.today_new_candidates} neutral />
              </div>
            </aside>
          </section>

          <section className="panel overflow-hidden">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-base font-semibold">最近活动</h2>
            </div>
            {dashboard.recent_activities.length === 0 ? (
              <div className="p-5">
                <EmptyState title="暂无活动记录" description="上传简历、修改状态和重新评分后会在这里形成记录。" />
              </div>
            ) : (
              <div className="divide-y divide-border">
                {dashboard.recent_activities.map((activity) => (
                  <div key={activity.id} className="flex items-start justify-between gap-4 px-5 py-4">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{activity.title}</p>
                      <p className="mt-1 truncate text-sm text-muted-foreground">{activity.description}</p>
                    </div>
                    <time className="shrink-0 text-xs text-muted-foreground">
                      {formatDateTime(activity.happened_at)}
                    </time>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}
    </WorkspaceShell>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof BriefcaseBusiness;
  label: string;
  value: number;
}) {
  return (
    <div className="panel px-4 py-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold text-muted-foreground">{label}</p>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function TodoIcon({ tone }: { tone: string }) {
  if (tone === "danger") return <AlertTriangle className="h-4 w-4 text-red-600" />;
  if (tone === "success") return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  return <Upload className="h-4 w-4 text-muted-foreground" />;
}

function AlertRow({ label, value, neutral = false }: { label: string; value: number; neutral?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={neutral || value === 0 ? "text-sm font-semibold" : "text-sm font-semibold text-red-600"}>
        {value}
      </span>
    </div>
  );
}
