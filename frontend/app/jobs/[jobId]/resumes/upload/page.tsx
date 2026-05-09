"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, useState } from "react";
import { ArrowLeft, FileText, Loader2, PencilLine, Upload } from "lucide-react";

import { ResumeUploadResult, retryParseResume, uploadResume } from "@/lib/api";

export default function ResumeUploadPage() {
  const params = useParams<{ jobId: string }>();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [results, setResults] = useState<ResumeUploadResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    setError(null);
    setResults([]);
    setFiles(Array.from(event.target.files ?? []));
  }

  async function handleUpload() {
    setError(null);
    setUploading(true);
    const nextResults: ResumeUploadResult[] = [];
    try {
      for (const file of files) {
        nextResults.push(await uploadResume(params.jobId, file));
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

  return (
    <main className="min-h-screen bg-muted px-6 py-8">
      <section className="mx-auto max-w-6xl">
        <Link href={`/jobs/${params.jobId}`} className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" />
          返回岗位详情
        </Link>

        <div className="mt-5">
          <h1 className="text-2xl font-semibold">上传简历</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            MVP 支持 PDF、DOCX、TXT。老版 DOC 和图片简历暂不进入第一版解析范围。
          </p>
        </div>

        {error ? (
          <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        <div className="mt-6 rounded-lg border border-border bg-background p-6">
          <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted px-6 text-center">
            <Upload className="h-8 w-8 text-muted-foreground" />
            <span className="mt-3 text-sm font-medium">选择简历文件</span>
            <span className="mt-1 text-xs text-muted-foreground">支持多选，单个文件不超过 10MB</span>
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
              <h2 className="text-sm font-semibold">待上传文件</h2>
              <div className="mt-3 divide-y divide-border rounded-lg border border-border">
                {files.map((file) => (
                  <div key={`${file.name}-${file.size}`} className="flex items-center gap-3 px-4 py-3 text-sm">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="flex-1 truncate">{file.name}</span>
                    <span className="text-xs text-muted-foreground">{Math.ceil(file.size / 1024)} KB</span>
                  </div>
                ))}
              </div>
              <button
                onClick={() => void handleUpload()}
                disabled={uploading}
                className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground disabled:opacity-60"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                开始上传并解析
              </button>
            </div>
          ) : null}
        </div>

        {results.length ? (
          <div className="mt-6 rounded-lg border border-border bg-background">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-base font-semibold">解析结果</h2>
            </div>
            <div className="divide-y divide-border">
              {results.map((result) => (
                <div key={result.resume_file.id} className="grid gap-3 px-5 py-4 text-sm md:grid-cols-[1.3fr_0.7fr_1fr_1fr]">
                  <div>
                    <p className="font-medium">{result.resume_file.file_name}</p>
                    {result.resume_file.parse_error ? (
                      <p className="mt-1 text-xs text-red-600">{result.resume_file.parse_error}</p>
                    ) : null}
                  </div>
                  <span className="text-muted-foreground">
                    {result.resume_file.parse_status === "success" ? "解析成功" : "解析失败"}
                  </span>
                  <span className="text-muted-foreground">
                    {result.candidate?.name || "姓名待确认"}
                  </span>
                  <span className="text-muted-foreground">
                    {result.candidate?.phone || "手机号待确认"}
                  </span>
                  <div className="md:col-span-4">
                    {result.candidate ? (
                      <Link
                        href={`/jobs/${params.jobId}/candidates/${result.candidate.id}/review`}
                        className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-background px-3 text-xs font-medium"
                      >
                        <PencilLine className="h-3.5 w-3.5" />
                        对照原简历修正
                      </Link>
                    ) : (
                      <button
                        onClick={() => void handleRetryParse(result.resume_file.id)}
                        disabled={retryingId === result.resume_file.id}
                        className="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-background px-3 text-xs font-medium disabled:opacity-60"
                      >
                        {retryingId === result.resume_file.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <PencilLine className="h-3.5 w-3.5" />
                        )}
                        重新解析
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
