"use client";

import Link from "next/link";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { AlertTriangle, Briefcase, CheckCircle2, FileText, Loader2, Upload } from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  JobListItem,
  ResumeUploadResult,
  listJobs,
  uploadResumeWithJob,
} from "@/lib/api";

export default function UnifiedResumeUploadPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [jobId, setJobId] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<ResumeUploadResult[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadJobs() {
      setLoadingJobs(true);
      setError(null);
      try {
        const rows = await listJobs();
        setJobs(rows);
        setJobId(rows.find((job) => job.status !== "closed")?.id ?? rows[0]?.id ?? "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "岗位加载失败");
      } finally {
        setLoadingJobs(false);
      }
    }
    void loadJobs();
  }, []);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    setError(null);
    setResults([]);
    setFiles(Array.from(event.target.files ?? []));
  }

  async function handleUpload() {
    if (!jobId) {
      setError("请先选择归属岗位");
      return;
    }
    if (!files.length) {
      setError("请先选择简历文件");
      return;
    }
    setUploading(true);
    setError(null);
    const nextResults: ResumeUploadResult[] = [];
    try {
      for (const file of files) {
        const result = await uploadResumeWithJob(jobId, file);
        nextResults.push(result);
        setResults([...nextResults]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "简历上传失败");
      setResults(nextResults);
    } finally {
      setUploading(false);
    }
  }

  const selectedJob = jobs.find((job) => job.id === jobId);
  const summary = useMemo(
    () => ({
      total: results.length,
      success: results.filter((result) => result.resume_file.parse_status === "success").length,
      duplicate: results.filter((result) => result.duplicate_candidates.length > 0).length,
    }),
    [results],
  );

  return (
    <WorkspaceShell
      title="统一上传简历"
      description="跨岗位上传入口。上传前选择归属岗位，系统会复用岗位内上传链路完成解析、评分和重复识别。"
      backHref="/dashboard"
      backLabel="返回工作台"
      actions={
        selectedJob ? (
          <Link href={`/jobs/${selectedJob.id}/candidates`} className="btn-secondary">
            查看归属岗位候选人
          </Link>
        ) : null
      }
    >
      {error ? <Notice tone="error">{error}</Notice> : null}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="panel p-5">
          <div className="mb-5">
            <label className="text-sm font-semibold" htmlFor="job-select">
              归属岗位
            </label>
            <select
              id="job-select"
              className="input mt-2"
              value={jobId}
              onChange={(event) => setJobId(event.target.value)}
              disabled={loadingJobs || uploading}
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} / {job.status}
                </option>
              ))}
            </select>
          </div>

          {loadingJobs ? (
            <div className="flex items-center gap-2 rounded-md bg-muted px-4 py-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              正在加载岗位
            </div>
          ) : jobs.length === 0 ? (
            <EmptyState title="暂无岗位" description="先创建岗位后，再上传归属到该岗位的简历。" />
          ) : (
            <>
              <label className="flex min-h-60 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-border bg-muted/70 px-6 text-center transition hover:border-primary hover:bg-primary/5">
                <Upload className="h-10 w-10 text-primary" />
                <span className="mt-3 text-base font-semibold">选择简历文件</span>
                <span className="mt-1 text-sm text-muted-foreground">支持 PDF、DOCX、TXT，多选后逐个上传</span>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  onChange={handleFiles}
                  disabled={uploading}
                />
              </label>

              {files.length ? (
                <div className="mt-5">
                  <div className="mb-3 flex items-center justify-between">
                    <h2 className="text-base font-semibold">待上传文件</h2>
                    <button onClick={() => void handleUpload()} disabled={uploading || !jobId} className="btn-primary">
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
            </>
          )}
        </section>

        <aside className="space-y-5">
          <section className="panel p-5">
            <h2 className="text-base font-semibold">归属岗位</h2>
            {selectedJob ? (
              <div className="mt-4 text-sm leading-6 text-muted-foreground">
                <div className="flex items-center gap-2 text-foreground">
                  <Briefcase className="h-4 w-4" />
                  <span className="font-semibold">{selectedJob.title}</span>
                </div>
                <p className="mt-2">状态：{selectedJob.status}</p>
                <p>候选人：{selectedJob.candidate_count}</p>
              </div>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">请选择岗位。</p>
            )}
          </section>
          <section className="panel p-5">
            <h2 className="text-base font-semibold">上传结果</h2>
            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
              <Summary label="完成" value={summary.total} />
              <Summary label="成功" value={summary.success} />
              <Summary label="重复风险" value={summary.duplicate} />
            </div>
          </section>
        </aside>
      </div>

      {results.length ? (
        <section className="panel mt-5 overflow-hidden">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold">上传明细</h2>
          </div>
          <div className="overflow-x-auto">
            <div className="data-grid-head grid-cols-[1.25fr_0.9fr_0.8fr_0.8fr_0.9fr_0.8fr]">
              <span>文件</span>
              <span>归属岗位</span>
              <span>状态</span>
              <span>候选人</span>
              <span>重复识别</span>
              <span>操作</span>
            </div>
            <div className="divide-y divide-border">
              {results.map((result) => (
                <div key={result.resume_file.id} className="data-grid-row grid-cols-[1.25fr_0.9fr_0.8fr_0.8fr_0.9fr_0.8fr]">
                  <span className="min-w-0 truncate font-medium">{result.resume_file.file_name}</span>
                  <span className="min-w-0 truncate text-muted-foreground">{selectedJob?.title ?? result.resume_file.job_id}</span>
                  <span className="flex items-center gap-1 text-muted-foreground">
                    {result.resume_file.parse_status === "success" ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : null}
                    {result.resume_file.parse_status === "success" ? "解析成功" : "解析失败"}
                  </span>
                  <span className="text-muted-foreground">{result.candidate?.name || "待确认"}</span>
                  <DuplicateSummary count={result.duplicate_candidates.length} />
                  <span>
                    {result.candidate ? (
                      <Link href={`/jobs/${result.resume_file.job_id}/candidates/${result.candidate.id}`} className="btn-secondary h-9 text-xs">
                        查看详情
                      </Link>
                    ) : (
                      <span className="text-xs text-muted-foreground">待处理</span>
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

function DuplicateSummary({ count }: { count: number }) {
  if (!count) return <span className="text-muted-foreground">无风险</span>;
  return (
    <span className="flex items-center gap-1 text-amber-700">
      <AlertTriangle className="h-4 w-4" />
      {count} 个疑似重复
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
