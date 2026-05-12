"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, FileText, Loader2, PencilLine, RefreshCw, Upload } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  ResumeUploadResult,
  UploadProcessingTask,
  listUploadTasks,
  retryFailedUploadTasks,
  retryParseResume,
  retryUploadTask,
  uploadResume,
} from "@/lib/api";

export default function ResumeUploadPage() {
  const params = useParams<{ jobId: string }>();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [retryingTasks, setRetryingTasks] = useState(false);
  const [results, setResults] = useState<ResumeUploadResult[]>([]);
  const [tasks, setTasks] = useState<UploadProcessingTask[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadTasks() {
    try {
      setTasks(await listUploadTasks(params.jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传任务加载失败");
    }
  }

  useEffect(() => {
    void loadTasks();
  }, []);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    setError(null);
    setResults([]);
    setFiles(Array.from(event.target.files ?? []));
  }

  async function handleUpload() {
    if (!files.length) {
      setError("请先选择简历文件");
      return;
    }
    setError(null);
    setUploading(true);
    const nextResults: ResumeUploadResult[] = [];
    try {
      for (const file of files) {
        nextResults.push(await uploadResume(params.jobId, file));
        await loadTasks();
      }
      setResults(nextResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : "简历上传失败");
      setResults(nextResults);
    } finally {
      setUploading(false);
    }
  }

  async function handleRetryParse(resumeFileId: string) {
    setRetryingId(resumeFileId);
    setError(null);
    try {
      const retried = await retryParseResume(resumeFileId);
      setResults((current) =>
        current.map((item) => (item.resume_file.id === resumeFileId ? retried : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新解析失败");
    } finally {
      setRetryingId(null);
    }
  }

  async function handleRetryTask(taskId: string) {
    setRetryingId(taskId);
    setError(null);
    try {
      const task = await retryUploadTask(params.jobId, taskId);
      setTasks((current) => current.map((item) => (item.id === taskId ? task : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务重试失败");
    } finally {
      setRetryingId(null);
    }
  }

  async function handleRetryFailedTasks() {
    setRetryingTasks(true);
    setError(null);
    try {
      const retried = await retryFailedUploadTasks(params.jobId);
      const byId = new Map(retried.map((task) => [task.id, task]));
      setTasks((current) => current.map((task) => byId.get(task.id) ?? task));
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量重试失败");
    } finally {
      setRetryingTasks(false);
    }
  }

  const summary = useMemo(
    () => ({
      total: tasks.length || results.length,
      success:
        tasks.length > 0
          ? tasks.filter((item) => item.parse_status === "success" && item.match_status === "success").length
          : results.filter((item) => item.resume_file.parse_status === "success").length,
      failed:
        tasks.length > 0
          ? tasks.filter((item) => item.parse_status === "failed" || item.match_status === "failed").length
          : results.filter((item) => item.resume_file.parse_status === "failed").length,
    }),
    [results, tasks],
  );

  const failedTasks = tasks.filter((task) => task.parse_status === "failed" || task.match_status === "failed");

  return (
    <WorkspaceShell
      title="上传简历"
      description="支持 PDF、DOCX、TXT。文件上传后会立即抽取文本、结构化字段并尝试生成匹配评分。"
      backHref={`/jobs/${params.jobId}`}
      backLabel="返回岗位详情"
      actions={
        <>
          <button onClick={() => void loadTasks()} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新任务
          </button>
          <Link href={`/jobs/${params.jobId}/candidates`} className="btn-secondary">
            查看候选人
          </Link>
        </>
      }
    >
      {error ? <Notice tone="error">{error}</Notice> : null}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="panel p-5">
          <label className="flex min-h-60 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-border bg-muted/70 px-6 text-center transition hover:border-primary hover:bg-primary/5">
            <Upload className="h-10 w-10 text-primary" />
            <span className="mt-3 text-base font-semibold">选择简历文件</span>
            <span className="mt-1 text-sm text-muted-foreground">支持多选，单个文件不超过 10MB</span>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={handleFiles}
            />
          </label>

          {files.length ? (
            <div className="mt-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-semibold">待上传文件</h2>
                <button onClick={() => void handleUpload()} disabled={uploading} className="btn-primary">
                  {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  开始上传
                </button>
              </div>
              <div className="divide-y divide-border rounded-md border border-border">
                {files.map((file) => (
                  <div key={`${file.name}-${file.size}`} className="flex items-center gap-3 px-4 py-3 text-sm">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="min-w-0 flex-1 truncate">{file.name}</span>
                    <span className="text-xs text-muted-foreground">{Math.ceil(file.size / 1024)} KB</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </section>

        <aside className="space-y-5">
          <section className="panel p-5">
            <h2 className="text-base font-semibold">解析进度</h2>
            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
              <Summary label="总数" value={summary.total} />
              <Summary label="成功" value={summary.success} />
              <Summary label="失败" value={summary.failed} />
            </div>
          </section>
          {failedTasks.length ? (
            <button onClick={() => void handleRetryFailedTasks()} disabled={retryingTasks} className="btn-primary w-full">
              {retryingTasks ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              重试失败项
            </button>
          ) : null}
          <section className="panel p-5 text-sm leading-6 text-muted-foreground">
            <h2 className="text-base font-semibold text-foreground">上传范围</h2>
            <p className="mt-3">MVP 暂不支持老版 DOC、图片简历和 ZIP 包。解析失败时可以在结果区重新解析。</p>
          </section>
        </aside>
      </div>

      {tasks.length ? (
        <section className="panel mt-5 overflow-hidden">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold">上传处理队列</h2>
          </div>
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
                  <DuplicateStatus count={task.duplicate_count} />
                  <span className="min-w-0 truncate text-xs text-red-600">{task.error_message || "-"}</span>
                  <span>
                    {task.parse_status === "failed" || task.match_status === "failed" ? (
                      <button
                        onClick={() => void handleRetryTask(task.id)}
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
        </section>
      ) : null}

      {results.length ? (
        <section className="panel mt-5 overflow-hidden">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold">解析结果</h2>
          </div>
          <div className="overflow-x-auto">
            <div className="data-grid-head grid-cols-[1.4fr_0.65fr_0.75fr_0.75fr_0.75fr_0.9fr]">
              <span>文件</span>
              <span>状态</span>
              <span>姓名</span>
              <span>手机号</span>
              <span>重复识别</span>
              <span>操作</span>
            </div>
            <div className="divide-y divide-border">
              {results.map((result) => (
                <div key={result.resume_file.id} className="data-grid-row grid-cols-[1.4fr_0.65fr_0.75fr_0.75fr_0.75fr_0.9fr]">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{result.resume_file.file_name}</p>
                    {result.resume_file.parse_error ? (
                      <p className="mt-1 truncate text-xs text-red-600">{result.resume_file.parse_error}</p>
                    ) : null}
                  </div>
                  <span className="flex items-center gap-1 text-muted-foreground">
                    {result.resume_file.parse_status === "success" ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : null}
                    {result.resume_file.parse_status === "success" ? "解析成功" : "解析失败"}
                  </span>
                  <span className="text-muted-foreground">{result.candidate?.name || "待确认"}</span>
                  <span className="text-muted-foreground">{result.candidate?.phone || "待确认"}</span>
                  <DuplicateStatus count={result.duplicate_candidates.length} />
                  <span>
                    {result.candidate ? (
                      <Link href={`/jobs/${params.jobId}/candidates/${result.candidate.id}/review`} className="btn-secondary h-9 text-xs">
                        <PencilLine className="h-3.5 w-3.5" />
                        修正
                      </Link>
                    ) : (
                      <button
                        onClick={() => void handleRetryParse(result.resume_file.id)}
                        disabled={retryingId === result.resume_file.id}
                        className="btn-secondary h-9 text-xs"
                      >
                        {retryingId === result.resume_file.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                        重新解析
                      </button>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : null}
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
  const isFailed = value === "failed";
  return <span className={isFailed ? "text-red-600" : "text-muted-foreground"}>{labels[value] ?? value}</span>;
}

function DuplicateStatus({ count }: { count: number }) {
  if (!count) return <span className="text-xs text-muted-foreground">无风险</span>;
  return (
    <span className="flex items-center gap-1 text-xs text-amber-700">
      <AlertTriangle className="h-3.5 w-3.5" />
      {count} 个
    </span>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-muted px-3 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
