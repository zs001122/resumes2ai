"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, Clipboard, Download, FileText, Loader2, PencilLine, RefreshCw } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  CandidateDetail,
  CandidateJobHistoryItem,
  CandidateMatch,
  CandidateMatchExplanation,
  CandidateNote,
  CandidateRecommendationReport,
  CandidateTag,
  CandidateTimelineEvent,
  addCandidateTag,
  addCandidateToTalentPool,
  createCandidateMatch,
  createCandidateNote,
  getCandidateDetail,
  getCandidateMatchExplanations,
  getCandidateRecommendationReport,
  listCandidateJobHistory,
  listCandidateNotes,
  listCandidateTags,
  listCandidateTimeline,
  removeCandidateFromTalentPool,
  removeCandidateTag,
  reviewCandidateDuplicateCheck,
} from "@/lib/api";

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function CandidateDetailPage() {
  const params = useParams<{ jobId: string; candidateId: string }>();
  const [detail, setDetail] = useState<CandidateDetail | null>(null);
  const [match, setMatch] = useState<CandidateMatch | null>(null);
  const [explanations, setExplanations] = useState<CandidateMatchExplanation[]>([]);
  const [notes, setNotes] = useState<CandidateNote[]>([]);
  const [timeline, setTimeline] = useState<CandidateTimelineEvent[]>([]);
  const [report, setReport] = useState<CandidateRecommendationReport | null>(null);
  const [reportText, setReportText] = useState("");
  const [tags, setTags] = useState<CandidateTag[]>([]);
  const [jobHistory, setJobHistory] = useState<CandidateJobHistoryItem[]>([]);
  const [noteText, setNoteText] = useState("");
  const [tagText, setTagText] = useState("");
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [savingNote, setSavingNote] = useState(false);
  const [savingTalentPool, setSavingTalentPool] = useState(false);
  const [savingTag, setSavingTag] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [copyingReport, setCopyingReport] = useState(false);
  const [reviewingDuplicateId, setReviewingDuplicateId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    setLoading(true);
    setError(null);
    try {
      const data = await getCandidateDetail(params.jobId, params.candidateId);
      setDetail(data);
      setMatch(data.match);
      if (data.match) {
        setExplanations(await getCandidateMatchExplanations(params.jobId, params.candidateId));
      } else {
        setExplanations([]);
      }
      setNotes(await listCandidateNotes(params.jobId, params.candidateId));
      setTimeline(await listCandidateTimeline(params.jobId, params.candidateId));
      setTags(await listCandidateTags(params.candidateId));
      setJobHistory(await listCandidateJobHistory(params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选人详情加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleAddToTalentPool() {
    setSavingTalentPool(true);
    setError(null);
    try {
      await addCandidateToTalentPool(params.candidateId, params.jobId);
      await loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : "加入人才库失败");
    } finally {
      setSavingTalentPool(false);
    }
  }

  async function handleRemoveFromTalentPool() {
    setSavingTalentPool(true);
    setError(null);
    try {
      await removeCandidateFromTalentPool(params.candidateId);
      await loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : "移出人才库失败");
    } finally {
      setSavingTalentPool(false);
    }
  }

  async function handleAddTag() {
    const name = tagText.trim();
    if (!name) return;
    setSavingTag(true);
    setError(null);
    try {
      await addCandidateTag(params.candidateId, name);
      setTagText("");
      setTags(await listCandidateTags(params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "标签保存失败");
    } finally {
      setSavingTag(false);
    }
  }

  async function handleRemoveTag(tagId: string) {
    setSavingTag(true);
    setError(null);
    try {
      await removeCandidateTag(params.candidateId, tagId);
      setTags(await listCandidateTags(params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "标签移除失败");
    } finally {
      setSavingTag(false);
    }
  }

  async function handleCreateNote() {
    const content = noteText.trim();
    if (!content) return;
    setSavingNote(true);
    setError(null);
    try {
      await createCandidateNote(params.jobId, params.candidateId, content);
      setNoteText("");
      setNotes(await listCandidateNotes(params.jobId, params.candidateId));
      setTimeline(await listCandidateTimeline(params.jobId, params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "备注保存失败");
    } finally {
      setSavingNote(false);
    }
  }

  async function handleRematch() {
    setMatching(true);
    setError(null);
    try {
      setMatch(await createCandidateMatch(params.jobId, params.candidateId));
      setExplanations(await getCandidateMatchExplanations(params.jobId, params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新评分失败");
    } finally {
      setMatching(false);
    }
  }

  async function handleReviewDuplicate(checkId: string, status: "ignored" | "confirmed_duplicate") {
    setReviewingDuplicateId(checkId);
    setError(null);
    try {
      const updated = await reviewCandidateDuplicateCheck(params.jobId, params.candidateId, checkId, status);
      setDetail((current) =>
        current
          ? {
              ...current,
              duplicate_candidates: current.duplicate_candidates.map((item) =>
                item.id === checkId ? updated : item,
              ),
            }
          : current,
      );
      setTimeline(await listCandidateTimeline(params.jobId, params.candidateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "重复复核保存失败");
    } finally {
      setReviewingDuplicateId(null);
    }
  }

  async function handleGenerateReport() {
    setGeneratingReport(true);
    setError(null);
    try {
      const generated = await getCandidateRecommendationReport(params.jobId, params.candidateId);
      setReport(generated);
      setReportText(generated.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "推荐摘要生成失败");
    } finally {
      setGeneratingReport(false);
    }
  }

  async function handleCopyReport() {
    if (!reportText.trim()) return;
    setCopyingReport(true);
    setError(null);
    try {
      await navigator.clipboard.writeText(reportText);
    } catch (err) {
      setError(err instanceof Error ? err.message : "复制失败，请手动选择文本复制");
    } finally {
      setCopyingReport(false);
    }
  }

  function handleDownloadReport() {
    if (!reportText.trim() || !detail) return;
    const blob = new Blob([reportText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const name = detail.candidate.name || params.candidateId;
    link.href = url;
    link.download = `${name}-推荐摘要.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
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

            <Panel title="重复识别">
              {detail.duplicate_candidates.length ? (
                <div className="space-y-3">
                  <div className="flex items-start gap-2 rounded-md bg-amber-50 px-3 py-3 text-sm text-amber-800">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <p>疑似重复，仅供 HR 复核，不自动合并。</p>
                  </div>
                  {detail.duplicate_candidates.map((item) => (
                    <div key={item.id} className="rounded-md border border-border px-3 py-3">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-semibold">{item.matched_candidate?.name || "姓名待确认"}</p>
                        <DuplicateReviewStatus status={item.status} />
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {item.match_reason} / 置信度 {Math.round(item.confidence * 100)}%
                      </p>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {item.matched_candidate?.phone || item.matched_candidate?.email || "联系方式待确认"}
                      </p>
                      {item.review_note ? (
                        <p className="mt-2 rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">{item.review_note}</p>
                      ) : null}
                      {item.status === "pending_review" ? (
                        <div className="mt-3 grid gap-2 sm:grid-cols-2">
                          <button
                            onClick={() => void handleReviewDuplicate(item.id, "ignored")}
                            disabled={reviewingDuplicateId === item.id}
                            className="btn-secondary h-9 text-xs"
                          >
                            {reviewingDuplicateId === item.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                            忽略风险
                          </button>
                          <button
                            onClick={() => void handleReviewDuplicate(item.id, "confirmed_duplicate")}
                            disabled={reviewingDuplicateId === item.id}
                            className="btn-primary h-9 text-xs"
                          >
                            {reviewingDuplicateId === item.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                            确认重复
                          </button>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">暂无疑似重复记录。</p>
              )}
            </Panel>

            <Panel title="人才库">
              <div className="flex flex-wrap gap-2">
                <button onClick={() => void handleAddToTalentPool()} disabled={savingTalentPool} className="btn-primary">
                  {savingTalentPool ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  加入人才库
                </button>
                <button onClick={() => void handleRemoveFromTalentPool()} disabled={savingTalentPool} className="btn-secondary">
                  移出人才库
                </button>
              </div>
              <div className="mt-4 flex gap-2">
                <input className="input" placeholder="新增标签" value={tagText} onChange={(event) => setTagText(event.target.value)} />
                <button onClick={() => void handleAddTag()} disabled={savingTag || !tagText.trim()} className="btn-secondary">
                  添加
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {tags.length ? (
                  tags.map((tag) => (
                    <button
                      key={tag.id}
                      onClick={() => void handleRemoveTag(tag.id)}
                      className="status-pill"
                      title="点击移除标签"
                    >
                      {tag.name}
                    </button>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">暂无标签</span>
                )}
              </div>
            </Panel>

            <Panel title="候选人备注">
              <textarea
                className="input min-h-28 resize-y"
                placeholder="记录电话沟通、用人部门反馈或后续跟进事项"
                value={noteText}
                onChange={(event) => setNoteText(event.target.value)}
              />
              <button onClick={() => void handleCreateNote()} disabled={savingNote || !noteText.trim()} className="btn-primary mt-3 w-full">
                {savingNote ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                保存备注
              </button>
              {notes.length ? (
                <div className="mt-4 space-y-3">
                  {notes.map((note) => (
                    <div key={note.id} className="rounded-md bg-muted px-3 py-3">
                      <p className="text-sm leading-6">{note.content}</p>
                      <p className="mt-2 text-xs text-muted-foreground">{formatDateTime(note.created_at)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-muted-foreground">暂无备注。</p>
              )}
            </Panel>
          </aside>

          <section className="space-y-5">
            {match ? (
              <div className="grid gap-4 md:grid-cols-2">
                <Panel title="分项解释">
                  {explanations.length ? (
                    <div className="space-y-3">
                      {explanations.map((item) => (
                        <div key={item.id} className="rounded-md bg-muted px-3 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-semibold">{item.dimension}</p>
                            <span className="text-sm font-semibold">{item.score ?? "-"}</span>
                          </div>
                          <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.conclusion}</p>
                          {item.evidence_text ? (
                            <p className="mt-2 rounded-md bg-background px-3 py-2 text-xs leading-5 text-muted-foreground">
                              {item.evidence_text}
                            </p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">暂无分项解释。</p>
                  )}
                </Panel>
                <List title="匹配点" items={match.matched_points} />
                <List title="短板" items={match.weak_points} />
                <List title="风险点" items={match.risks} />
                <List title="面试问题" items={match.interview_questions} />
              </div>
            ) : null}

            <Panel title="推荐摘要">
              <div className="flex flex-wrap gap-2">
                <button onClick={() => void handleGenerateReport()} disabled={generatingReport || !match} className="btn-primary">
                  {generatingReport ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  生成推荐摘要
                </button>
                <button onClick={() => void handleCopyReport()} disabled={copyingReport || !reportText.trim()} className="btn-secondary">
                  {copyingReport ? <Loader2 className="h-4 w-4 animate-spin" /> : <Clipboard className="h-4 w-4" />}
                  复制 Markdown
                </button>
                <button onClick={handleDownloadReport} disabled={!reportText.trim()} className="btn-secondary">
                  <Download className="h-4 w-4" />
                  下载 .md
                </button>
              </div>
              {!match ? (
                <p className="mt-3 text-sm text-muted-foreground">请先生成匹配评分，再生成推荐摘要。</p>
              ) : null}
              {report ? (
                <p className="mt-3 text-xs text-muted-foreground">
                  已生成 Markdown 草稿，可在导出前人工调整。
                </p>
              ) : null}
              <textarea
                className="input mt-4 min-h-96 resize-y font-mono text-sm leading-6"
                placeholder="生成后可在这里编辑推荐摘要"
                value={reportText}
                onChange={(event) => setReportText(event.target.value)}
              />
            </Panel>

            <Panel title="原简历预览">
              <p className="mb-3 text-sm text-muted-foreground">{detail.resume_file.file_name}</p>
              <div className="max-h-[720px] overflow-auto whitespace-pre-wrap rounded-md bg-muted p-4 text-sm leading-7">
                {renderHighlightedPreview(
                  detail.preview.content,
                  [...detail.candidate.skills, ...explanations.map((item) => item.evidence_text || "")].filter(Boolean),
                )}
              </div>
            </Panel>

            <Panel title="操作时间线">
              {timeline.length ? (
                <div className="space-y-3">
                  {timeline.map((event) => (
                    <div key={event.id} className="rounded-md border border-border px-3 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{event.action_summary}</p>
                        <time className="text-xs text-muted-foreground">{formatDateTime(event.created_at)}</time>
                      </div>
                      {event.after_value || event.before_value ? (
                        <p className="mt-2 text-sm text-muted-foreground">
                          {event.after_value || event.before_value}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">暂无时间线记录。</p>
              )}
            </Panel>

            <Panel title="历史岗位">
              {jobHistory.length ? (
                <div className="space-y-3">
                  {jobHistory.map((item) => (
                    <div key={item.job_id} className="rounded-md border border-border px-3 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <Link href={`/jobs/${item.job_id}`} className="text-sm font-semibold text-primary">
                          {item.job_title}
                        </Link>
                        <span className="status-pill">{item.candidate_status}</span>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">
                        岗位状态：{item.job_status} / 更新于 {formatDateTime(item.updated_at)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">暂无历史岗位。</p>
              )}
            </Panel>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}

function DuplicateReviewStatus({ status }: { status: string }) {
  const labels: Record<string, string> = {
    pending_review: "待复核",
    ignored: "已忽略",
    confirmed_duplicate: "确认重复",
  };
  const tone =
    status === "confirmed_duplicate"
      ? "bg-red-50 text-red-700"
      : status === "ignored"
        ? "bg-emerald-50 text-emerald-700"
        : "bg-amber-50 text-amber-700";
  return <span className={`shrink-0 rounded px-2 py-1 text-xs font-semibold ${tone}`}>{labels[status] ?? status}</span>;
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

function renderHighlightedPreview(content: string, keywords: string[]): ReactNode[] {
  const ranges = keywords.flatMap((keyword) => findAllRanges(content, keyword));
  const merged = mergeRanges(ranges, content.length);
  const nodes: ReactNode[] = [];
  let cursor = 0;
  for (const range of merged) {
    if (range.start > cursor) {
      nodes.push(content.slice(cursor, range.start));
    }
    nodes.push(
      <mark key={`${range.start}-${range.end}`} className="rounded-sm bg-emerald-100 px-0.5 text-emerald-950">
        {content.slice(range.start, range.end)}
      </mark>,
    );
    cursor = range.end;
  }
  if (cursor < content.length) {
    nodes.push(content.slice(cursor));
  }
  return nodes;
}

function findAllRanges(content: string, keyword: string): Array<{ start: number; end: number }> {
  if (!keyword.trim()) return [];
  const ranges: Array<{ start: number; end: number }> = [];
  const lowerContent = content.toLowerCase();
  const lowerKeyword = keyword.toLowerCase();
  let index = lowerContent.indexOf(lowerKeyword);
  while (index >= 0) {
    ranges.push({ start: index, end: index + keyword.length });
    index = lowerContent.indexOf(lowerKeyword, index + keyword.length);
  }
  return ranges;
}

function mergeRanges(ranges: Array<{ start: number; end: number }>, maxLength: number) {
  const sorted = ranges
    .map((range) => ({
      start: Math.max(0, Math.min(maxLength, range.start)),
      end: Math.max(0, Math.min(maxLength, range.end)),
    }))
    .filter((range) => range.end > range.start)
    .sort((a, b) => a.start - b.start || b.end - a.end);
  const result: Array<{ start: number; end: number }> = [];
  for (const range of sorted) {
    const previous = result[result.length - 1];
    if (!previous || range.start >= previous.end) {
      result.push(range);
    }
  }
  return result;
}
