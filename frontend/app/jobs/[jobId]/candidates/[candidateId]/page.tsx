"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  Archive,
  BadgeCheck,
  BriefcaseBusiness,
  CheckCircle2,
  Clipboard,
  Download,
  FileSearch,
  FileText,
  History,
  Loader2,
  Mail,
  MapPin,
  PencilLine,
  Phone,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Tag,
  UserRound,
} from "lucide-react";

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
  ResumeParseRun,
  addCandidateTag,
  addCandidateToTalentPool,
  createCandidateMatch,
  createCandidateNote,
  getCandidateDetail,
  getCandidateMatchExplanations,
  getCandidateRecommendationReport,
  getLatestResumeParseRun,
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

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return `${Math.round(value)}%`;
}

export default function CandidateDetailPage() {
  const params = useParams<{ jobId: string; candidateId: string }>();
  const [detail, setDetail] = useState<CandidateDetail | null>(null);
  const [match, setMatch] = useState<CandidateMatch | null>(null);
  const [explanations, setExplanations] = useState<CandidateMatchExplanation[]>([]);
  const [parseRun, setParseRun] = useState<ResumeParseRun | null>(null);
  const [notes, setNotes] = useState<CandidateNote[]>([]);
  const [timeline, setTimeline] = useState<CandidateTimelineEvent[]>([]);
  const [report, setReport] = useState<CandidateRecommendationReport | null>(null);
  const [reportText, setReportText] = useState("");
  const [tags, setTags] = useState<CandidateTag[]>([]);
  const [jobHistory, setJobHistory] = useState<CandidateJobHistoryItem[]>([]);
  const [activeEvidenceText, setActiveEvidenceText] = useState<string | null>(null);
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
      setParseRun(null);
      if (data.match) {
        setExplanations(await getCandidateMatchExplanations(params.jobId, params.candidateId));
      } else {
        setExplanations([]);
      }
      try {
        setParseRun(await getLatestResumeParseRun(data.resume_file.id));
      } catch {
        setParseRun(null);
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

  const selectedFieldCount = useMemo(
    () => parseRun?.field_candidates.filter((item) => item.selected).length ?? 0,
    [parseRun],
  );
  const evidenceKeywords = useMemo(
    () =>
      [
        activeEvidenceText,
        ...(detail?.candidate.skills ?? []),
        ...explanations.map((item) => item.evidence_text || ""),
      ].filter((item): item is string => Boolean(item?.trim())),
    [activeEvidenceText, detail?.candidate.skills, explanations],
  );
  const pendingDuplicateCount = detail?.duplicate_candidates.filter((item) => item.status === "pending_review").length ?? 0;

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
        <>
          <button onClick={() => void loadDetail()} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新
          </button>
          <Link href={`/jobs/${params.jobId}/candidates/${params.candidateId}/review`} className="btn-primary">
            <PencilLine className="h-4 w-4" />
            修正解析结果
          </Link>
        </>
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
        <div className="space-y-5">
          <section className="panel overflow-hidden">
            <div className="grid gap-0 xl:grid-cols-[1fr_320px]">
              <div className="p-5 sm:p-6">
                <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-slate-900 text-sm font-semibold text-white">
                        {(detail.candidate.name || "候").slice(0, 1)}
                      </span>
                      <div>
                        <h2 className="text-xl font-semibold text-foreground">{detail.candidate.name || "姓名待确认"}</h2>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {detail.candidate.current_title || "岗位待确认"} · {detail.candidate.current_company || "公司待确认"}
                        </p>
                      </div>
                    </div>
                    <div className="mt-5 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2 xl:grid-cols-4">
                      <Signal icon={Phone} label="电话" value={detail.candidate.phone || "待确认"} />
                      <Signal icon={Mail} label="邮箱" value={detail.candidate.email || "待确认"} />
                      <Signal icon={MapPin} label="城市" value={detail.candidate.city || "待确认"} />
                      <Signal
                        icon={BriefcaseBusiness}
                        label="年限 / 学历"
                        value={`${detail.candidate.years_of_experience ?? "-"} 年 / ${detail.candidate.highest_education || "-"}`}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 lg:w-[360px]">
                    <DecisionMetric label="匹配分" value={match ? String(Math.round(match.score)) : "-"} tone={scoreTone(match?.score)} />
                    <DecisionMetric label="低置信" value={String(detail.candidate.low_confidence_fields.length)} tone={detail.candidate.low_confidence_fields.length ? "warning" : "success"} />
                    <DecisionMetric label="重复待复核" value={String(pendingDuplicateCount)} tone={pendingDuplicateCount ? "warning" : "default"} />
                  </div>
                </div>
              </div>
              <div className="border-t border-border bg-slate-50 p-5 xl:border-l xl:border-t-0">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">解析质量</p>
                    <p className="mt-1 text-2xl font-semibold">{formatPercent(parseRun?.quality_score)}</p>
                  </div>
                  <FileSearch className="h-8 w-8 text-slate-400" />
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <MiniMetric label="字段候选" value={parseRun ? `${selectedFieldCount}/${parseRun.field_candidates.length}` : "-"} />
                  <MiniMetric label="段落块" value={String(parseRun?.blocks.length ?? "-")} />
                </div>
                {parseRun?.warnings.length ? (
                  <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">
                    {parseRun.warnings[0]}
                  </p>
                ) : null}
              </div>
            </div>
          </section>

          <div className="grid gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
            <aside className="space-y-5 xl:sticky xl:top-5 xl:self-start">
              <Panel title="匹配决策" icon={<Sparkles className="h-4 w-4" />}>
                {match ? (
                  <div className="space-y-4">
                    <div className="flex items-end justify-between gap-4">
                      <div>
                        <p className="text-4xl font-semibold leading-none">{Math.round(match.score)}</p>
                        <p className="mt-2 text-sm font-medium text-muted-foreground">{match.level}</p>
                      </div>
                      <button onClick={() => void handleRematch()} disabled={matching} className="btn-secondary h-9 text-xs">
                        {matching ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                        重评
                      </button>
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">{match.summary}</p>
                  </div>
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

              <Panel title="人才库与标签" icon={<Archive className="h-4 w-4" />}>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => void handleAddToTalentPool()} disabled={savingTalentPool} className="btn-primary h-9 text-xs">
                    {savingTalentPool ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                    加入人才库
                  </button>
                  <button onClick={() => void handleRemoveFromTalentPool()} disabled={savingTalentPool} className="btn-secondary h-9 text-xs">
                    移出人才库
                  </button>
                </div>
                <div className="mt-4 flex gap-2">
                  <input className="input h-9 py-1 text-sm" placeholder="新增标签" value={tagText} onChange={(event) => setTagText(event.target.value)} />
                  <button onClick={() => void handleAddTag()} disabled={savingTag || !tagText.trim()} className="btn-secondary h-9 text-xs">
                    添加
                  </button>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {tags.length ? (
                    tags.map((tag) => (
                      <button key={tag.id} onClick={() => void handleRemoveTag(tag.id)} className="status-pill" title="点击移除标签">
                        <Tag className="mr-1 h-3 w-3" />
                        {tag.name}
                      </button>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">暂无标签</span>
                  )}
                </div>
              </Panel>

              <Panel title="重复风险" icon={<ShieldAlert className="h-4 w-4" />}>
                <DuplicateReviewList
                  items={detail.duplicate_candidates}
                  reviewingDuplicateId={reviewingDuplicateId}
                  onReview={(id, status) => void handleReviewDuplicate(id, status)}
                />
              </Panel>

              <Panel title="备注" icon={<Clipboard className="h-4 w-4" />}>
                <textarea
                  className="input min-h-24 resize-y text-sm"
                  placeholder="记录电话沟通、用人部门反馈或后续跟进事项"
                  value={noteText}
                  onChange={(event) => setNoteText(event.target.value)}
                />
                <button onClick={() => void handleCreateNote()} disabled={savingNote || !noteText.trim()} className="btn-primary mt-3 h-9 w-full text-xs">
                  {savingNote ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                  保存备注
                </button>
                <div className="mt-4 space-y-3">
                  {notes.slice(0, 3).map((note) => (
                    <div key={note.id} className="border-l-2 border-slate-200 pl-3">
                      <p className="text-sm leading-6">{note.content}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(note.created_at)}</p>
                    </div>
                  ))}
                  {!notes.length ? <p className="text-sm text-muted-foreground">暂无备注。</p> : null}
                </div>
              </Panel>
            </aside>

            <section className="space-y-5">
              <Panel title="分项解释" icon={<BadgeCheck className="h-4 w-4" />} actions={<span className="text-xs text-muted-foreground">{explanations.length} 项</span>}>
                {match ? (
                  <div className="grid gap-3 lg:grid-cols-2">
                    {explanations.length ? (
                      explanations.map((item) => (
                        <EvidenceRow key={item.id} title={item.dimension} score={item.score} body={item.conclusion} evidence={item.evidence_text} />
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">暂无分项解释。</p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">生成匹配评分后会展示分项解释。</p>
                )}
              </Panel>

              {match ? (
                <div className="grid gap-5 lg:grid-cols-2">
                  <InsightList title="匹配点" items={match.matched_points} tone="success" />
                  <InsightList title="短板" items={match.weak_points} tone="warning" />
                  <InsightList title="风险点" items={match.risks} tone="danger" />
                  <InsightList title="面试问题" items={match.interview_questions} tone="default" />
                </div>
              ) : null}

              <Panel title="vNext 解析证据" icon={<FileSearch className="h-4 w-4" />}>
                {parseRun ? (
                  <div className="space-y-4">
                    <div className="grid gap-3 lg:grid-cols-[1.1fr_1fr]">
                      <div className="grid gap-3 sm:grid-cols-3">
                        <MiniMetric label="Parser" value={parseRun.parser_version} />
                        <MiniMetric label="AI 增强" value={parseRun.ai_enabled ? "已开启" : "未开启"} />
                        <MiniMetric label="质量分" value={formatPercent(parseRun.quality_score)} />
                      </div>
                      <LowConfidenceSummary fields={detail.candidate.low_confidence_fields} />
                    </div>
                    <FieldCandidateTable
                      parseRun={parseRun}
                      lowConfidenceFields={detail.candidate.low_confidence_fields}
                      onFocusEvidence={setActiveEvidenceText}
                    />
                    <ParseBlocks blocks={parseRun.blocks} onFocusEvidence={setActiveEvidenceText} />
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">暂无 vNext 解析运行记录。重新上传或重新解析后会生成。</p>
                )}
              </Panel>

              <Panel title="结构化简历" icon={<UserRound className="h-4 w-4" />}>
                <div className="grid gap-5 lg:grid-cols-2">
                  <ProfileFacts detail={detail} />
                  <div>
                    <TagList title="技能" items={detail.candidate.skills} />
                    <TagList title="证书" items={detail.candidate.certifications} />
                    <TagList title="语言" items={detail.candidate.languages} />
                    <InlineList title="奖项荣誉" items={detail.candidate.awards} />
                  </div>
                </div>
                <div className="mt-5 grid gap-5 lg:grid-cols-3">
                  <StructuredItems title="教育经历" items={detail.candidate.education} />
                  <StructuredItems title="工作经历" items={detail.candidate.work_experiences} />
                  <StructuredItems title="项目经历" items={detail.candidate.project_experiences} />
                </div>
                {detail.candidate.self_evaluation ? (
                  <div className="mt-5 border-t border-border pt-4">
                    <p className="text-sm font-semibold">自我评价</p>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{detail.candidate.self_evaluation}</p>
                  </div>
                ) : null}
              </Panel>

              <Panel
                title="原简历预览"
                icon={<FileText className="h-4 w-4" />}
                actions={<span className="truncate text-xs text-muted-foreground">{detail.resume_file.file_name}</span>}
              >
                {activeEvidenceText ? (
                  <div className="mb-3 flex flex-col gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900 sm:flex-row sm:items-center sm:justify-between">
                    <span className="min-w-0 truncate">已高亮证据：{activeEvidenceText}</span>
                    <button onClick={() => setActiveEvidenceText(null)} className="btn-secondary h-8 shrink-0 bg-white text-xs">
                      清除高亮
                    </button>
                  </div>
                ) : null}
                <div className="max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md border border-border bg-slate-50 p-4 text-sm leading-7">
                  {renderHighlightedPreview(detail.preview.content, evidenceKeywords)}
                </div>
              </Panel>

              <Panel title="推荐摘要" icon={<FileText className="h-4 w-4" />}>
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
                {!match ? <p className="mt-3 text-sm text-muted-foreground">请先生成匹配评分，再生成推荐摘要。</p> : null}
                {report ? <p className="mt-3 text-xs text-muted-foreground">已生成 Markdown 草稿，可在导出前人工调整。</p> : null}
                <textarea
                  className="input mt-4 min-h-80 resize-y font-mono text-sm leading-6"
                  placeholder="生成后可在这里编辑推荐摘要"
                  value={reportText}
                  onChange={(event) => setReportText(event.target.value)}
                />
              </Panel>

              <div className="grid gap-5 lg:grid-cols-2">
                <TimelinePanel timeline={timeline} />
                <JobHistoryPanel jobHistory={jobHistory} />
              </div>
            </section>
          </div>
        </div>
      )}
    </WorkspaceShell>
  );
}

function Signal({ icon: Icon, label, value }: { icon: typeof Phone; label: string; value: string }) {
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-md border border-border bg-white px-3 py-2">
      <Icon className="h-4 w-4 shrink-0 text-slate-400" />
      <div className="min-w-0">
        <p className="text-[11px] font-semibold text-muted-foreground">{label}</p>
        <p className="truncate text-sm font-medium text-foreground">{value}</p>
      </div>
    </div>
  );
}

function DecisionMetric({ label, value, tone }: { label: string; value: string; tone: "success" | "warning" | "danger" | "default" }) {
  const toneClass = {
    success: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
    danger: "border-red-200 bg-red-50 text-red-800",
    default: "border-border bg-white text-foreground",
  }[tone];
  return (
    <div className={`rounded-md border px-3 py-3 ${toneClass}`}>
      <p className="text-[11px] font-semibold opacity-75">{label}</p>
      <p className="mt-1 text-2xl font-semibold leading-none">{value}</p>
    </div>
  );
}

function scoreTone(score: number | undefined): "success" | "warning" | "danger" | "default" {
  if (score === undefined) return "default";
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "danger";
}

function Panel({ title, icon, actions, children }: { title: string; icon?: ReactNode; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-border bg-slate-50/80 px-5 py-4">
        <h2 className="flex items-center gap-2 text-base font-semibold">
          {icon ? <span className="text-muted-foreground">{icon}</span> : null}
          {title}
        </h2>
        {actions}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-white px-3 py-2">
      <p className="text-[11px] font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  );
}

function ProfileFacts({ detail }: { detail: CandidateDetail }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Info label="邮箱" value={detail.candidate.email} />
      <Info label="当前公司" value={detail.candidate.current_company} />
      <Info label="工作年限" value={detail.candidate.years_of_experience?.toString()} />
      <Info label="最高学历" value={detail.candidate.highest_education} />
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-md border border-border px-3 py-3">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value || "待确认"}</p>
    </div>
  );
}

function EvidenceRow({ title, score, body, evidence }: { title: string; score: number | null; body: string; evidence: string | null }) {
  return (
    <div className="rounded-md border border-border p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">{title}</p>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{score ?? "-"}</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
      {evidence ? <p className="mt-3 border-l-2 border-emerald-300 pl-3 text-xs leading-5 text-muted-foreground">{evidence}</p> : null}
    </div>
  );
}

function InsightList({ title, items, tone }: { title: string; items: string[]; tone: "success" | "warning" | "danger" | "default" }) {
  const Icon = tone === "success" ? CheckCircle2 : tone === "danger" ? AlertTriangle : tone === "warning" ? ShieldAlert : FileText;
  return (
    <Panel title={title} icon={<Icon className="h-4 w-4" />}>
      {items.length ? (
        <ul className="space-y-2 text-sm text-muted-foreground">
          {items.map((item) => (
            <li key={item} className="border-l-2 border-slate-200 pl-3 leading-6">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">暂无</p>
      )}
    </Panel>
  );
}


function LowConfidenceSummary({ fields }: { fields: string[] }) {
  return (
    <div className="rounded-md border border-border bg-white px-3 py-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-semibold text-muted-foreground">低置信字段</p>
        <span className={fields.length ? "text-xs font-semibold text-amber-700" : "text-xs font-semibold text-emerald-700"}>
          {fields.length ? `${fields.length} 项待复核` : "无明显风险"}
        </span>
      </div>
      {fields.length ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {fields.map((field) => (
            <span key={field} className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
              {fieldLabel(field)}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">核心字段解析置信度稳定。</p>
      )}
    </div>
  );
}

function FieldCandidateTable({
  parseRun,
  lowConfidenceFields,
  onFocusEvidence,
}: {
  parseRun: ResumeParseRun;
  lowConfidenceFields: string[];
  onFocusEvidence: (text: string) => void;
}) {
  const [filter, setFilter] = useState<"all" | "selected" | "review">("all");
  const lowConfidenceSet = useMemo(() => new Set(lowConfidenceFields), [lowConfidenceFields]);
  const sortedCandidates = useMemo(
    () =>
      [...parseRun.field_candidates].sort((a, b) => {
        const riskDelta = Number(lowConfidenceSet.has(b.field_name)) - Number(lowConfidenceSet.has(a.field_name));
        if (riskDelta) return riskDelta;
        const selectedDelta = Number(b.selected) - Number(a.selected);
        if (selectedDelta) return selectedDelta;
        return (a.confidence ?? -1) - (b.confidence ?? -1);
      }),
    [lowConfidenceSet, parseRun.field_candidates],
  );
  const candidates = sortedCandidates.filter((item) => {
    if (filter === "selected") return item.selected;
    if (filter === "review") return !item.selected || lowConfidenceSet.has(item.field_name);
    return true;
  });
  const selectedCount = parseRun.field_candidates.filter((item) => item.selected).length;
  const reviewCount = parseRun.field_candidates.filter((item) => !item.selected || lowConfidenceSet.has(item.field_name)).length;

  return (
    <div className="overflow-hidden rounded-md border border-border">
      <div className="flex flex-col gap-3 border-b border-border bg-slate-50 px-3 py-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold">字段候选</p>
          <p className="mt-1 text-xs text-muted-foreground">展示候选值、抽取器、置信度和原文证据。</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <FilterButton active={filter === "all"} onClick={() => setFilter("all")}>全部 {parseRun.field_candidates.length}</FilterButton>
          <FilterButton active={filter === "selected"} onClick={() => setFilter("selected")}>已选 {selectedCount}</FilterButton>
          <FilterButton active={filter === "review"} onClick={() => setFilter("review")}>待复核 {reviewCount}</FilterButton>
        </div>
      </div>
      {candidates.length ? (
        <div className="divide-y divide-border">
          {candidates.map((item) => {
            const isLowConfidence = lowConfidenceSet.has(item.field_name);
            return (
              <div key={item.id} className="grid gap-3 px-3 py-3 lg:grid-cols-[180px_minmax(0,1fr)_160px]">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold">{fieldLabel(item.field_name)}</p>
                    {isLowConfidence ? <span className="rounded bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">低置信</span> : null}
                    <span className={item.selected ? "rounded bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700" : "rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600"}>
                      {item.selected ? "已采用" : "未采用"}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">{item.extractor}</p>
                </div>
                <div className="min-w-0">
                  <p className="line-clamp-2 text-sm leading-6 text-foreground" title={stringifyValue(item.value_json)}>
                    {stringifyValue(item.value_json) || "-"}
                  </p>
                  {item.source_text ? (
                    <div className="mt-2 rounded-md bg-slate-50 px-3 py-2">
                      <p className="line-clamp-2 text-xs leading-5 text-muted-foreground">{item.source_text}</p>
                      <button onClick={() => onFocusEvidence(item.source_text || "")} className="mt-2 text-xs font-semibold text-primary hover:underline">
                        高亮原文证据
                      </button>
                    </div>
                  ) : (
                    <p className="mt-2 text-xs text-muted-foreground">暂无原文证据。</p>
                  )}
                  {item.rejection_reason ? <p className="mt-2 text-xs text-amber-700">未采用原因：{item.rejection_reason}</p> : null}
                </div>
                <ConfidenceCell confidence={item.confidence} />
              </div>
            );
          })}
        </div>
      ) : (
        <p className="px-3 py-4 text-sm text-muted-foreground">当前筛选下暂无字段候选。</p>
      )}
    </div>
  );
}

function FilterButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={active ? "rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white" : "rounded-md border border-border bg-white px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground"}
    >
      {children}
    </button>
  );
}

function ConfidenceCell({ confidence }: { confidence: number | null }) {
  const percent = confidence === null ? null : Math.round(confidence * 100);
  const tone = confidence === null ? "bg-slate-200" : confidence >= 0.8 ? "bg-emerald-500" : confidence >= 0.6 ? "bg-amber-500" : "bg-red-500";
  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-muted-foreground">置信度</p>
        <span className="text-sm font-semibold">{percent === null ? "-" : `${percent}%`}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${percent ?? 0}%` }} />
      </div>
    </div>
  );
}

function ParseBlocks({ blocks, onFocusEvidence }: { blocks: ResumeParseRun["blocks"]; onFocusEvidence: (text: string) => void }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">段落识别</p>
        <span className="text-xs text-muted-foreground">{blocks.length} 个段落块</span>
      </div>
      {blocks.length ? (
        <div className="grid gap-3 lg:grid-cols-2">
          {blocks.slice(0, 8).map((block) => (
            <div key={block.id} className="rounded-md border border-border px-3 py-3">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">{block.title || block.block_type}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{block.block_type}{block.inferred ? " / 推断段落" : ""}</p>
                </div>
                <span className="shrink-0 text-xs font-semibold text-muted-foreground">{Math.round((block.confidence ?? 0) * 100)}%</span>
              </div>
              <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs leading-5 text-muted-foreground">{block.text}</p>
              <button onClick={() => onFocusEvidence(block.text)} className="mt-3 text-xs font-semibold text-primary hover:underline">
                高亮该段原文
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">暂无段落识别结果。</p>
      )}
    </div>
  );
}

function DuplicateReviewList({
  items,
  reviewingDuplicateId,
  onReview,
}: {
  items: CandidateDetail["duplicate_candidates"];
  reviewingDuplicateId: string | null;
  onReview: (id: string, status: "ignored" | "confirmed_duplicate") => void;
}) {
  if (!items.length) return <p className="text-sm text-muted-foreground">暂无疑似重复记录。</p>;
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2 rounded-md bg-amber-50 px-3 py-3 text-sm text-amber-800">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <p>疑似重复，仅供 HR 复核，不自动合并。</p>
      </div>
      {items.map((item) => (
        <div key={item.id} className="rounded-md border border-border px-3 py-3">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-semibold">{item.matched_candidate?.name || "姓名待确认"}</p>
            <DuplicateReviewStatus status={item.status} />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{item.match_reason} / 置信度 {Math.round(item.confidence * 100)}%</p>
          <p className="mt-2 text-xs text-muted-foreground">{item.matched_candidate?.phone || item.matched_candidate?.email || "联系方式待确认"}</p>
          {item.review_note ? <p className="mt-2 text-xs text-muted-foreground">{item.review_note}</p> : null}
          {item.status === "pending_review" ? (
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <button onClick={() => onReview(item.id, "ignored")} disabled={reviewingDuplicateId === item.id} className="btn-secondary h-9 text-xs">
                {reviewingDuplicateId === item.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                忽略
              </button>
              <button onClick={() => onReview(item.id, "confirmed_duplicate")} disabled={reviewingDuplicateId === item.id} className="btn-primary h-9 text-xs">
                {reviewingDuplicateId === item.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                确认
              </button>
            </div>
          ) : null}
        </div>
      ))}
    </div>
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

function TagList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4 first:mt-0">
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

function InlineList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-muted-foreground">{title}</p>
      {items.length ? (
        <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
          {items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">暂无</p>
      )}
    </div>
  );
}

function StructuredItems({ title, items }: { title: string; items: Record<string, unknown>[] }) {
  return (
    <div>
      <p className="text-sm font-semibold">{title}</p>
      {items.length ? (
        <div className="mt-2 space-y-2">
          {items.map((item, index) => (
            <div key={`${title}-${index}`} className="rounded-md border border-border px-3 py-3 text-sm leading-6 text-muted-foreground">
              {formatStructuredItem(item)}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">暂无</p>
      )}
    </div>
  );
}

function TimelinePanel({ timeline }: { timeline: CandidateTimelineEvent[] }) {
  return (
    <Panel title="操作时间线" icon={<History className="h-4 w-4" />}>
      {timeline.length ? (
        <div className="space-y-3">
          {timeline.slice(0, 8).map((event) => (
            <div key={event.id} className="border-l-2 border-slate-200 pl-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold">{event.action_summary}</p>
                <time className="text-xs text-muted-foreground">{formatDateTime(event.created_at)}</time>
              </div>
              {event.after_value || event.before_value ? <p className="mt-1 text-sm text-muted-foreground">{event.after_value || event.before_value}</p> : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">暂无时间线记录。</p>
      )}
    </Panel>
  );
}

function JobHistoryPanel({ jobHistory }: { jobHistory: CandidateJobHistoryItem[] }) {
  return (
    <Panel title="历史岗位" icon={<BriefcaseBusiness className="h-4 w-4" />}>
      {jobHistory.length ? (
        <div className="space-y-3">
          {jobHistory.map((item) => (
            <div key={item.job_id} className="rounded-md border border-border px-3 py-3">
              <div className="flex items-center justify-between gap-3">
                <Link href={`/jobs/${item.job_id}`} className="text-sm font-semibold text-primary">{item.job_title}</Link>
                <span className="status-pill">{item.candidate_status}</span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">岗位状态：{item.job_status} / 更新于 {formatDateTime(item.updated_at)}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">暂无历史岗位。</p>
      )}
    </Panel>
  );
}

function formatStructuredItem(item: Record<string, unknown>) {
  const preferred = ["time_range", "school", "degree", "major", "company", "title", "name", "role", "description", "raw"];
  const values = preferred
    .map((key) => item[key])
    .filter((value) => typeof value === "string" && value.trim())
    .map(String);
  if (values.length) return values.join(" / ");
  return JSON.stringify(item);
}

function fieldLabel(fieldName: string) {
  const labels: Record<string, string> = {
    name: "姓名",
    phone: "手机号",
    email: "邮箱",
    city: "城市",
    years_of_experience: "工作年限",
    highest_education: "最高学历",
    current_company: "当前公司",
    current_title: "当前岗位",
    skills: "技能",
    education: "教育经历",
    work_experiences: "工作经历",
    project_experiences: "项目经历",
    certifications: "证书",
    languages: "语言",
    awards: "奖项",
    self_evaluation: "自我评价",
  };
  return labels[fieldName] ?? fieldName;
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map((item) => stringifyValue(item)).filter(Boolean).join("、");
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const preferred = ["name", "school", "company", "title", "degree", "description", "raw"];
    const parts = preferred.map((key) => record[key]).filter((item) => typeof item === "string" && item.trim()).map(String);
    return parts.length ? parts.join(" / ") : JSON.stringify(value);
  }
  return "";
}

function renderHighlightedPreview(content: string, keywords: string[]): ReactNode[] {
  const ranges = keywords.flatMap((keyword) => findAllRanges(content, keyword));
  const merged = mergeRanges(ranges, content.length);
  const nodes: ReactNode[] = [];
  let cursor = 0;
  for (const range of merged) {
    if (range.start > cursor) nodes.push(content.slice(cursor, range.start));
    nodes.push(
      <mark key={`${range.start}-${range.end}`} className="rounded-sm bg-emerald-100 px-0.5 text-emerald-950">
        {content.slice(range.start, range.end)}
      </mark>,
    );
    cursor = range.end;
  }
  if (cursor < content.length) nodes.push(content.slice(cursor));
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
    .map((range) => ({ start: Math.max(0, Math.min(maxLength, range.start)), end: Math.max(0, Math.min(maxLength, range.end)) }))
    .filter((range) => range.end > range.start)
    .sort((a, b) => a.start - b.start || b.end - a.end);
  const result: Array<{ start: number; end: number }> = [];
  for (const range of sorted) {
    const previous = result[result.length - 1];
    if (!previous || range.start >= previous.end) result.push(range);
  }
  return result;
}
