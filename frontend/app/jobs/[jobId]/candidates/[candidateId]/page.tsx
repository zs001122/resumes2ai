"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Loader2, PencilLine, RefreshCw } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
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
    <WorkspaceShell
      title={detail?.candidate.name || "候选人详情"}
      description={
        detail
          ? `${detail.candidate.current_title || "岗位待确认"} / ${detail.candidate.city || "城市待确认"} / ${detail.candidate.phone || "联系方式待确认"}`
          : "查看 AI 匹配分析、结构化信息和原简历。"
      }
      backHref={`/jobs/${params.jobId}/candidates`}
      backLabel="返回候选人列表"
      actions={
        <Link href={`/jobs/${params.jobId}/candidates/${params.candidateId}/review`} className="btn-primary">
          <PencilLine className="h-4 w-4" />
          修正解析结果
        </Link>
      }
    >
      {error ? (
        <Notice
          tone="error"
          action={
            <button onClick={() => void loadDetail()} className="btn-secondary h-8 text-xs">
              重试
            </button>
          }
        >
          {error}
        </Notice>
      ) : null}

      {loading || !detail ? (
        <div className="panel flex items-center gap-2 p-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          正在加载候选人详情
        </div>
      ) : (
        <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="space-y-5">
            <Panel title="AI 匹配分析">
              {match ? (
                <>
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <p className="text-4xl font-semibold">{match.score}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{match.level}</p>
                    </div>
                    <button onClick={() => void handleRematch()} disabled={matching} className="btn-secondary h-9 text-xs">
                      {matching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                      重评
                    </button>
                  </div>
                  <p className="mt-4 text-sm leading-6 text-muted-foreground">{match.summary}</p>
                </>
              ) : (
                <div className="text-sm text-muted-foreground">
                  <p>暂无匹配结果。</p>
                  <button onClick={() => void handleRematch()} disabled={matching} className="btn-secondary mt-3 h-9 text-xs">
                    {matching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                    立即评分
                  </button>
                </div>
              )}
            </Panel>

            <Panel title="结构化信息">
              <Info label="邮箱" value={detail.candidate.email} />
              <Info label="当前公司" value={detail.candidate.current_company} />
              <Info label="工作年限" value={detail.candidate.years_of_experience?.toString()} />
              <Info label="最高学历" value={detail.candidate.highest_education} />
              <TagList title="技能" items={detail.candidate.skills} />
            </Panel>
          </aside>

          <section className="space-y-5">
            {match ? (
              <div className="grid gap-4 md:grid-cols-2">
                <List title="匹配点" items={match.matched_points} />
                <List title="短板" items={match.weak_points} />
                <List title="风险点" items={match.risks} />
                <List title="面试问题" items={match.interview_questions} />
              </div>
            ) : null}

            <Panel title="原简历预览">
              <p className="mb-3 text-sm text-muted-foreground">{detail.resume_file.file_name}</p>
              <pre className="max-h-[720px] overflow-auto whitespace-pre-wrap rounded-md bg-muted p-4 text-sm leading-7">
                {detail.preview.content}
              </pre>
            </Panel>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="panel p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "待确认"}</p>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <Panel title={title}>
      {items.length ? (
        <ul className="space-y-2 text-sm text-muted-foreground">
          {items.map((item) => (
            <li key={item} className="rounded-md bg-muted px-3 py-2">{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">暂无</p>
      )}
    </Panel>
  );
}

function TagList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-muted-foreground">{title}</p>
      {items.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {items.map((item) => (
            <span key={item} className="status-pill">{item}</span>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">暂无</p>
      )}
    </div>
  );
}
