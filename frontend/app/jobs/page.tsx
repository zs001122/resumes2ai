"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BriefcaseBusiness, Loader2, MapPin, Plus, RefreshCw } from "lucide-react";

import { JobListItem, listJobs } from "@/lib/api";

function statusLabel(status: JobListItem["status"]) {
  return status === "open" ? "开放中" : "已关闭";
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

  return (
    <main className="min-h-screen bg-muted px-6 py-8">
      <section className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">岗位列表</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              创建岗位、确认筛选标准，并从这里进入候选人筛选流程。
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => void loadJobs()}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-medium"
            >
              <RefreshCw className="h-4 w-4" />
              刷新
            </button>
            <Link
              href="/jobs/new"
              className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
            >
              <Plus className="h-4 w-4" />
              创建岗位
            </Link>
          </div>
        </div>

        {error ? (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            加载失败：{error}
          </div>
        ) : null}

        <div className="mt-6 overflow-hidden rounded-lg border border-border bg-background">
          <div className="grid grid-cols-[1.4fr_1fr_1fr_0.7fr_0.8fr] border-b border-border px-4 py-3 text-xs font-medium text-muted-foreground">
            <span>岗位</span>
            <span>部门</span>
            <span>地点</span>
            <span>状态</span>
            <span>创建时间</span>
          </div>

          {loading ? (
            <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              正在加载岗位
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-8 text-sm text-muted-foreground">
              暂无岗位。先创建一个岗位，再上传简历进行筛选。
            </div>
          ) : (
            <div className="divide-y divide-border">
              {jobs.map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="grid grid-cols-[1.4fr_1fr_1fr_0.7fr_0.8fr] items-center px-4 py-4 text-sm transition hover:bg-muted"
                >
                  <span className="flex items-center gap-2 font-medium">
                    <BriefcaseBusiness className="h-4 w-4 text-muted-foreground" />
                    {job.title}
                  </span>
                  <span className="text-muted-foreground">{job.department || "未填写"}</span>
                  <span className="flex items-center gap-1 text-muted-foreground">
                    <MapPin className="h-3.5 w-3.5" />
                    {job.location || "未填写"}
                  </span>
                  <span>
                    <span className="rounded-full bg-muted px-2 py-1 text-xs">
                      {statusLabel(job.status)}
                    </span>
                  </span>
                  <span className="text-muted-foreground">{formatDate(job.created_at)}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
