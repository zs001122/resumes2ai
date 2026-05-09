"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ListFilter, Loader2, RefreshCw, Upload } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
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
            <Link href={`/jobs/${job.id}/candidates`} className="btn-secondary">
              <ListFilter className="h-4 w-4" />
              候选人
            </Link>
            {job.status === "open" ? (
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
                <span className="status-pill">{job.status === "open" ? "开放中" : "已关闭"}</span>
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
                <Link href={`/jobs/${job.id}/candidates`} className="btn-secondary w-full">
                  查看候选人
                </Link>
              </div>
            </section>
          </aside>

          <section className="space-y-5">
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
          </section>
        </div>
      ) : (
        <div className="panel p-8 text-sm text-muted-foreground">未找到岗位。</div>
      )}
    </WorkspaceShell>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "未填写"}</p>
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
