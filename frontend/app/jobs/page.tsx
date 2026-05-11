"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { BriefcaseBusiness, Loader2, Plus, RefreshCw } from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import { JobListItem, listJobs } from "@/lib/api";

function statusLabel(status: JobListItem["status"]) {
  if (status === "open") return "开放中";
  if (status === "paused") return "已暂停";
  return "已关闭";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadJobs() {
    setLoading(true);
    setError(null);
    try {
      setJobs(await listJobs());
    } catch (err) {
      setError(err instanceof Error ? err.message : "岗位列表加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadJobs();
  }, []);

  const stats = useMemo(
    () => ({
      total: jobs.length,
      open: jobs.filter((job) => job.status === "open").length,
      candidates: jobs.reduce((sum, job) => sum + job.candidate_count, 0),
      high: jobs.reduce((sum, job) => sum + job.high_match_count, 0),
    }),
    [jobs],
  );

  return (
    <WorkspaceShell
      title="岗位工作台"
      description="从岗位开始组织筛选流程，快速查看每个岗位的候选人数量、强匹配数量和待处理情况。"
      actions={
        <>
          <button onClick={() => void loadJobs()} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新
          </button>
          <Link href="/jobs/new" className="btn-primary">
            <Plus className="h-4 w-4" />
            创建岗位
          </Link>
        </>
      }
    >
      {error ? (
        <Notice
          tone="error"
          action={
            <button onClick={() => void loadJobs()} className="btn-secondary h-8 text-xs">
              重试
            </button>
          }
        >
          {error}
        </Notice>
      ) : null}

      <div className="mb-5 grid gap-3 md:grid-cols-4">
        <Stat label="岗位总数" value={stats.total} />
        <Stat label="开放中" value={stats.open} />
        <Stat label="候选人" value={stats.candidates} />
        <Stat label="强匹配" value={stats.high} />
      </div>

      <section className="panel overflow-hidden">
        <div className="border-b border-border px-5 py-4">
          <h2 className="text-base font-semibold">岗位列表</h2>
        </div>
        {loading ? (
          <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在加载岗位
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="暂无岗位"
              description="先创建一个岗位，确认筛选标准后再上传简历。"
              action={
                <Link href="/jobs/new" className="btn-primary">
                  创建岗位
                </Link>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="data-grid-head grid-cols-[1.4fr_0.8fr_0.8fr_0.7fr_0.7fr_0.7fr_0.8fr]">
              <span>岗位</span>
              <span>部门</span>
              <span>地点</span>
              <span>候选人</span>
              <span>强匹配</span>
              <span>状态</span>
              <span>创建时间</span>
            </div>
            <div className="divide-y divide-border">
              {jobs.map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="data-grid-row grid-cols-[1.4fr_0.8fr_0.8fr_0.7fr_0.7fr_0.7fr_0.8fr]"
                >
                  <span className="flex min-w-0 items-center gap-2 font-medium">
                    <BriefcaseBusiness className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="truncate">{job.title}</span>
                  </span>
                  <span className="text-muted-foreground">{job.department || "未填写"}</span>
                  <span className="text-muted-foreground">{job.location || "未填写"}</span>
                  <span>{job.candidate_count}</span>
                  <span>{job.high_match_count}</span>
                  <span>
                    <span className="status-pill">{statusLabel(job.status)}</span>
                  </span>
                  <span className="text-muted-foreground">{formatDate(job.created_at)}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel px-4 py-3">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
