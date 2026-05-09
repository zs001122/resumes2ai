"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ArrowLeft, Loader2, PencilLine, RefreshCw } from "lucide-react";

import {
  CandidateDetail,
  CandidateMatch,
  createCandidateMatch,
  getCandidateDetail,
} from "@/lib/api";

export default function CandidateDetailPage() {
  const params = useParams<{ jobId: string; candidateId: string }>();
  const [detail, setDetail] = useState<CandidateDetail | null>(null);
  const [match, setMatch] = useState<CandidateMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    setLoading(true);
    setError(null);
    try {
      const data = await getCandidateDetail(params.jobId, params.candidateId);
      setDetail(data);
      setMatch(data.match);
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选人详情加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleRematch() {
    setMatching(true);
    setError(null);
    try {
      setMatch(await createCandidateMatch(params.jobId, params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新评分失败");
    } finally {
      setMatching(false);
    }
  }

  useEffect(() => {
    void loadDetail();
  }, [params.jobId, params.candidateId]);

  return (
    <main className="min-h-screen bg-muted px-6 py-8">
      <section className="mx-auto max-w-7xl">
        <Link href={`/jobs/${params.jobId}/candidates`} className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" />
          返回候选人列表
        </Link>

        {error ? <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> : null}

        {loading || !detail ? (
          <div className="mt-6 flex items-center gap-2 rounded-lg border border-border bg-background p-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在加载候选人详情
          </div>
        ) : (
          <>
            <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-2xl font-semibold">{detail.candidate.name || "姓名待确认"}</h1>
                <p className="mt-2 text-sm text-muted-foreground">
                  {detail.candidate.current_title || "岗位待确认"} · {detail.candidate.city || "城市待确认"} · {detail.candidate.phone || "手机号待确认"}
                </p>
              </div>
              <Link
                href={`/jobs/${params.jobId}/candidates/${params.candidateId}/review`}
                className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
              >
                <PencilLine className="h-4 w-4" />
                编辑解析结果
              </Link>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
              <div className="space-y-6">
                <Panel title="AI 匹配分析">
                  {match ? (
                    <div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-3xl font-semibold">{match.score}</p>
                          <p className="mt-1 text-sm text-muted-foreground">{match.level}</p>
                        </div>
                        <button
                          onClick={() => void handleRematch()}
                          disabled={matching}
                          className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-xs font-medium disabled:opacity-60"
                        >
                          {matching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                          重新评分
                        </button>
                      </div>
                      <p className="mt-4 text-sm leading-6 text-muted-foreground">{match.summary}</p>
                      <List title="匹配点" items={match.matched_points} />
                      <List title="短板" items={match.weak_points} />
                      <List title="风险点" items={match.risks} />
                      <List title="面试问题" items={match.interview_questions} />
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">暂无匹配结果</p>
                  )}
                </Panel>

                <Panel title="结构化信息">
                  <Info label="邮箱" value={detail.candidate.email} />
                  <Info label="当前公司" value={detail.candidate.current_company} />
                  <Info label="工作年限" value={detail.candidate.years_of_experience?.toString()} />
                  <Info label="最高学历" value={detail.candidate.highest_education} />
                  <List title="技能" items={detail.candidate.skills} />
                </Panel>
              </div>

              <Panel title="原简历预览">
                <p className="mb-3 text-sm text-muted-foreground">{detail.resume_file.file_name}</p>
                <pre className="max-h-[760px] overflow-auto whitespace-pre-wrap rounded-lg bg-muted p-4 text-sm leading-7">
                  {detail.preview.content}
                </pre>
              </Panel>
            </div>
          </>
        )}
      </section>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-background p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="mt-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "待确认"}</p>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-medium text-muted-foreground">{title}</p>
      {items.length ? (
        <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
          {items.map((item) => (
            <li key={item} className="rounded-md bg-muted px-3 py-2">{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">暂无</p>
      )}
    </div>
  );
}
