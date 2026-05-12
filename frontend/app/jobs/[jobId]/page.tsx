"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertTriangle, Copy, History, ListFilter, Loader2, Pause, Play, RefreshCw, Upload } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  closeJob,
  copyJob,
  getJDQuality,
  getJob,
  getJobFunnel,
  Job,
  JDQualityCheck,
  JobFunnelStats,
  JobStandardVersion,
  listJobStandardVersions,
  pauseJob,
  reopenJob,
} from "@/lib/api";

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
  const [funnel, setFunnel] = useState<JobFunnelStats | null>(null);
  const [quality, setQuality] = useState<JDQualityCheck | null>(null);
  const [standardVersions, setStandardVersions] = useState<JobStandardVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [closing, setClosing] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadJob() {
    setLoading(true);
    setError(null);
    try {
      const loadedJob = await getJob(params.jobId);
      setJob(loadedJob);
      setFunnel(await getJobFunnel(params.jobId));
      setQuality(await getJDQuality(params.jobId));
      setStandardVersions(await listJobStandardVersions(params.jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "岗位详情加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!job) return;
    setStatusSaving(true);
    setError(null);
    try {
      const copied = await copyJob(job.id);
      router.push(`/jobs/${copied.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "复制岗位失败");
    } finally {
      setStatusSaving(false);
    }
  }

  async function handlePause() {
    if (!job) return;
    setStatusSaving(true);
    setError(null);
    try {
      setJob(await pauseJob(job.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "暂停岗位失败");
    } finally {
      setStatusSaving(false);
    }
  }

  async function handleReopen() {
    if (!job) return;
    setStatusSaving(true);
    setError(null);
    try {
      setJob(await reopenJob(job.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新开放岗位失败");
    } finally {
      setStatusSaving(false);
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
    <WorkspaceShell
      title={job?.title ?? "岗位详情"}
      description={
        job
          ? `${job.department || "未填写部门"} / ${job.location || "未填写地点"} / 更新于 ${formatDate(job.updated_at)}`
          : "查看岗位信息、JD 和筛选标准。"
      }
      backHref="/jobs"
      backLabel="返回岗位列表"
      actions={
        job ? (
          <>
            <Link href={`/jobs/${job.id}/resumes/upload`} className="btn-primary">
              <Upload className="h-4 w-4" />
              上传简历
            </Link>
            <Link href={`/jobs/${job.id}/upload-tasks`} className="btn-secondary">
              <RefreshCw className="h-4 w-4" />
              上传队列
            </Link>
            <Link href={`/jobs/${job.id}/candidates`} className="btn-secondary">
              <ListFilter className="h-4 w-4" />
              候选人
            </Link>
            <button onClick={() => void handleCopy()} disabled={statusSaving} className="btn-secondary">
              <Copy className="h-4 w-4" />
              复制岗位
            </button>
            {job.status === "open" ? (
              <button onClick={() => void handlePause()} disabled={statusSaving} className="btn-secondary">
                {statusSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Pause className="h-4 w-4" />}
                暂停
              </button>
            ) : null}
            {job.status === "paused" ? (
              <button onClick={() => void handleReopen()} disabled={statusSaving} className="btn-secondary">
                {statusSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                重新开放
              </button>
            ) : null}
            {job.status !== "closed" ? (
              <button onClick={() => void handleClose()} disabled={closing} className="btn-danger">
                {closing ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                关闭岗位
              </button>
            ) : null}
          </>
        ) : null
      }
    >
      {error ? (
        <Notice
          tone="error"
          action={
            <button onClick={() => void loadJob()} className="btn-secondary h-8 text-xs">
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
          正在加载岗位详情
        </div>
      ) : job ? (
        <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="space-y-5">
            <section className="panel p-5">
              <div className="flex items-center justify-between gap-3 border-b border-border pb-4">
                <h2 className="text-base font-semibold">基础信息</h2>
                <span className="status-pill">{statusLabel(job.status)}</span>
              </div>
              <Info label="薪资范围" value={job.salary_range} />
              <Info label="年限要求" value={job.experience_required} />
              <Info label="学历要求" value={job.education_required} />
              <Info label="创建时间" value={formatDate(job.created_at)} />
            </section>

            <section className="panel p-5">
              <h2 className="text-base font-semibold">下一步</h2>
              <div className="mt-4 space-y-2">
                <Link href={`/jobs/${job.id}/resumes/upload`} className="btn-primary w-full">
                  上传简历
                </Link>
                <Link href={`/jobs/${job.id}/upload-tasks`} className="btn-secondary w-full">
                  查看上传队列
                </Link>
                <Link href={`/jobs/${job.id}/candidates`} className="btn-secondary w-full">
                  查看候选人
                </Link>
              </div>
            </section>

            <section className="panel p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-base font-semibold">标准版本</h2>
                <History className="h-4 w-4 text-muted-foreground" />
              </div>
              {standardVersions.length ? (
                <div className="mt-4 space-y-3">
                  <div className="rounded-md bg-muted px-3 py-3">
                    <p className="text-sm font-semibold">当前版本 v{standardVersions[0].version}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{standardVersions[0].change_summary}</p>
                  </div>
                  {standardVersions.length > 1 ? (
                    <div className="flex items-start gap-2 rounded-md bg-amber-50 px-3 py-3 text-sm text-amber-800">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      <p>岗位标准已变更，建议对历史候选人重新评分以保持口径一致。</p>
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="mt-3 text-sm text-muted-foreground">暂无版本记录。</p>
              )}
            </section>

            {quality ? (
              <section className="panel p-5">
                <h2 className="text-base font-semibold">JD 质量</h2>
                <p className="mt-2 text-3xl font-semibold">{quality.score}</p>
                {quality.issues.length ? (
                  <div className="mt-4 space-y-2">
                    {quality.issues.map((issue) => (
                      <p key={issue} className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                        {issue}
                      </p>
                    ))}
                  </div>
                ) : null}
                {quality.suggestions.length ? (
                  <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                    {quality.suggestions.map((suggestion) => (
                      <li key={suggestion}>• {suggestion}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ) : null}
          </aside>

          <section className="space-y-5">
            {funnel ? (
              <div className="grid gap-3 md:grid-cols-4">
                <FunnelStat label="已上传" value={funnel.uploaded} />
                <FunnelStat label="高匹配" value={funnel.high_match} />
                <FunnelStat label="待沟通" value={funnel.pending_contact} />
                <FunnelStat label="待复核" value={funnel.needs_review} />
                <FunnelStat label="待筛选" value={funnel.pending} />
                <FunnelStat label="已收藏" value={funnel.favorite} />
                <FunnelStat label="已淘汰" value={funnel.rejected} />
                <FunnelStat label="已入库" value={funnel.archived} />
              </div>
            ) : null}

            <div className="panel p-5">
              <h2 className="text-base font-semibold">岗位 JD</h2>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{job.jd}</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <ListPanel title="岗位职责" items={job.responsibilities} />
              <ListPanel title="必备条件" items={job.must_have} />
              <ListPanel title="加分条件" items={job.nice_to_have} />
              <ListPanel title="排除条件" items={job.deal_breakers} />
              <ListPanel title="评分维度" items={job.scoring_dimensions} />
            </div>

            <div className="panel p-5">
              <h2 className="text-base font-semibold">版本历史</h2>
              {standardVersions.length ? (
                <div className="mt-4 divide-y divide-border rounded-md border border-border">
                  {standardVersions.map((version) => (
                    <div key={version.id} className="px-4 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="text-sm font-semibold">v{version.version}</p>
                        <time className="text-xs text-muted-foreground">{formatDate(version.created_at)}</time>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{version.change_summary}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-muted-foreground">暂无版本历史。</p>
              )}
            </div>
          </section>
        </div>
      ) : (
        <div className="panel p-8 text-sm text-muted-foreground">未找到岗位。</div>
      )}
    </WorkspaceShell>
  );
}

function statusLabel(status: Job["status"]) {
  if (status === "open") return "开放中";
  if (status === "paused") return "已暂停";
  return "已关闭";
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "未填写"}</p>
    </div>
  );
}

function FunnelStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel px-4 py-3">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function ListPanel({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="panel p-5">
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
