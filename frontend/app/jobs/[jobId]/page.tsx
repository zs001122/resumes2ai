"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Loader2, Upload } from "lucide-react";

import { closeJob, getJob, Job } from "@/lib/api";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function JobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [closing, setClosing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadJob() {
    setLoading(true);
    setError(null);
    try {
      setJob(await getJob(params.jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "岗位详情加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleClose() {
    if (!job) return;
    setClosing(true);
    setError(null);
    try {
      setJob(await closeJob(job.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "关闭岗位失败");
    } finally {
      setClosing(false);
    }
  }

  useEffect(() => {
    void loadJob();
  }, [params.jobId]);

  return (
    <main className="min-h-screen bg-muted px-6 py-8">
      <section className="mx-auto max-w-6xl">
        <button
          onClick={() => router.push("/jobs")}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          返回岗位列表
        </button>

        {error ? (
          <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="mt-6 flex items-center gap-2 rounded-lg border border-border bg-background p-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在加载岗位详情
          </div>
        ) : job ? (
          <>
            <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-semibold">{job.title}</h1>
                  <span className="rounded-full bg-background px-3 py-1 text-xs text-muted-foreground">
                    {job.status === "open" ? "开放中" : "已关闭"}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {job.department || "未填写部门"} · {job.location || "未填写地点"} · 更新于 {formatDate(job.updated_at)}
                </p>
              </div>
              <div className="flex gap-2">
                <Link
                  href={`/jobs/${job.id}/resumes/upload`}
                  className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
                >
                  <Upload className="h-4 w-4" />
                  上传简历
                </Link>
                {job.status === "open" ? (
                  <button
                    onClick={() => void handleClose()}
                    disabled={closing}
                    className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-background px-4 text-sm font-medium disabled:opacity-60"
                  >
                    {closing ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    关闭岗位
                  </button>
                ) : null}
              </div>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
              <div className="rounded-lg border border-border bg-background p-5">
                <h2 className="text-base font-semibold">基础信息</h2>
                <Info label="薪资范围" value={job.salary_range} />
                <Info label="年限要求" value={job.experience_required} />
                <Info label="学历要求" value={job.education_required} />
                <Info label="创建时间" value={formatDate(job.created_at)} />
              </div>

              <div className="rounded-lg border border-border bg-background p-5">
                <h2 className="text-base font-semibold">岗位 JD</h2>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{job.jd}</p>
              </div>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              <ListPanel title="岗位职责" items={job.responsibilities} />
              <ListPanel title="必备条件" items={job.must_have} />
              <ListPanel title="加分条件" items={job.nice_to_have} />
              <ListPanel title="排除条件" items={job.deal_breakers} />
              <ListPanel title="评分维度" items={job.scoring_dimensions} />
            </div>
          </>
        ) : (
          <div className="mt-6 rounded-lg border border-border bg-background p-8 text-sm text-muted-foreground">
            未找到岗位。
          </div>
        )}
      </section>
    </main>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="mt-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "未填写"}</p>
    </div>
  );
}

function ListPanel({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-border bg-background p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
          {items.map((item) => (
            <li key={item} className="rounded-md bg-muted px-3 py-2">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">暂无内容</p>
      )}
    </div>
  );
}
