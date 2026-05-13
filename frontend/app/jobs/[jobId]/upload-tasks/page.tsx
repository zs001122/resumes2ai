"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Loader2, RefreshCw, Upload } from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  UploadProcessingTask,
  listUploadTasks,
  retryFailedUploadTasks,
  retryUploadTask,
} from "@/lib/api";

export default function UploadTasksPage() {
  const params = useParams<{ jobId: string }>();
  const [tasks, setTasks] = useState<UploadProcessingTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [retryingFailed, setRetryingFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadTasks() {
    setLoading(true);
    setError(null);
    try {
      setTasks(await listUploadTasks(params.jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传任务加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function retryTask(taskId: string) {
    setRetryingId(taskId);
    setError(null);
    try {
      const retried = await retryUploadTask(params.jobId, taskId);
      setTasks((current) => current.map((task) => (task.id === taskId ? retried : task)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务重试失败");
    } finally {
      setRetryingId(null);
    }
  }

  async function retryFailed() {
    setRetryingFailed(true);
    setError(null);
    try {
      const retried = await retryFailedUploadTasks(params.jobId);
      const byId = new Map(retried.map((task) => [task.id, task]));
      setTasks((current) => current.map((task) => byId.get(task.id) ?? task));
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量重试失败");
    } finally {
      setRetryingFailed(false);
    }
  }

  useEffect(() => {
    void loadTasks();
  }, []);

  const summary = useMemo(
    () => ({
      total: tasks.length,
      done: tasks.filter((task) => task.parse_status === "success" && task.match_status === "success").length,
      failed: tasks.filter((task) => task.parse_status === "failed" || task.match_status === "failed").length,
    }),
    [tasks],
  );

  return (
    <WorkspaceShell
      title="上传处理队列"
      description="查看当前岗位下每份简历的上传、解析和评分状态，并处理失败项。"
      backHref={`/jobs/${params.jobId}`}
      backLabel="返回岗位详情"
      actions={
        <>
          <button onClick={() => void loadTasks()} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新
          </button>
          <Link href={`/jobs/${params.jobId}/resumes/upload`} className="btn-primary">
            <Upload className="h-4 w-4" />
            上传简历
          </Link>
        </>
      }
    >
      {error ? <Notice tone="error">{error}</Notice> : null}

      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <Summary label="任务总数" value={summary.total} />
        <Summary label="已完成" value={summary.done} />
        <Summary label="失败项" value={summary.failed} />
      </div>

      {summary.failed ? (
        <div className="mb-5">
          <button onClick={() => void retryFailed()} disabled={retryingFailed} className="btn-primary">
            {retryingFailed ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            重试全部失败项
          </button>
        </div>
      ) : null}

      <section className="panel overflow-hidden">
        <div className="border-b border-border px-5 py-4">
          <h2 className="text-base font-semibold">任务列表</h2>
        </div>
        {loading ? (
          <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在加载上传任务
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="暂无上传任务"
              description="上传简历后，这里会显示每个文件的处理状态。"
              action={
                <Link href={`/jobs/${params.jobId}/resumes/upload`} className="btn-primary">
                  上传简历
                </Link>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="data-grid-head grid-cols-[1.4fr_0.6fr_0.6fr_0.6fr_0.6fr_1fr_0.7fr]">
              <span>文件</span>
              <span>上传</span>
              <span>解析</span>
              <span>评分</span>
              <span>重复</span>
              <span>失败原因</span>
              <span>操作</span>
            </div>
            <div className="divide-y divide-border">
              {tasks.map((task) => (
                <div key={task.id} className="data-grid-row grid-cols-[1.4fr_0.6fr_0.6fr_0.6fr_0.6fr_1fr_0.7fr]">
                  <span className="min-w-0 truncate font-medium">{task.original_filename}</span>
                  <StatusText value={task.upload_status} />
                  <StatusText value={task.parse_status} />
                  <StatusText value={task.match_status} />
                  <DuplicateStatus count={task.duplicate_count} task={task} />
                  <span className="min-w-0 truncate text-xs text-red-600">{task.error_message || "-"}</span>
                  <span>
                    {task.parse_status === "failed" || task.match_status === "failed" ? (
                      <button
                        onClick={() => void retryTask(task.id)}
                        disabled={retryingId === task.id}
                        className="btn-secondary h-9 text-xs"
                      >
                        {retryingId === task.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <RefreshCw className="h-3.5 w-3.5" />
                        )}
                        重试
                      </button>
                    ) : (
                      <span className="text-xs text-muted-foreground">无需操作</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}

function StatusText({ value }: { value: string }) {
  const labels: Record<string, string> = {
    pending: "等待中",
    uploaded: "已上传",
    success: "成功",
    failed: "失败",
    skipped: "跳过",
  };
  return <span className={value === "failed" ? "text-red-600" : "text-muted-foreground"}>{labels[value] ?? value}</span>;
}

function DuplicateStatus({ count, task }: { count: number; task?: UploadProcessingTask }) {
  if (!count) return <span className="text-xs text-muted-foreground">无风险</span>;
  const pending = task?.pending_duplicate_review_count ?? 0;
  const confirmed = task?.confirmed_duplicate_count ?? 0;
  const ignored = task?.ignored_duplicate_count ?? 0;
  return (
    <span className="space-y-1 text-xs">
      <span className="flex items-center gap-1 text-amber-700">
        <AlertTriangle className="h-3.5 w-3.5" />
        {pending ? `${pending} 待复核` : `${count} 个`}
      </span>
      {confirmed || ignored ? (
        <span className="block text-muted-foreground">
          {confirmed ? `确认 ${confirmed}` : ""}
          {confirmed && ignored ? " / " : ""}
          {ignored ? `忽略 ${ignored}` : ""}
        </span>
      ) : null}
    </span>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel px-4 py-3">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
