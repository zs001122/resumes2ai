"use client";

import { useParams } from "next/navigation";
import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, FileSearch, Loader2, RefreshCw, Save } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  CandidateMatch,
  CandidateReviewData,
  ResumeFieldCandidate,
  ResumeParseRun,
  createCandidateMatch,
  getCandidateMatch,
  getCandidateReviewData,
  getLatestResumeParseRun,
  updateCandidate,
} from "@/lib/api";

type EditableForm = {
  name: string;
  phone: string;
  email: string;
  city: string;
  current_company: string;
  current_title: string;
  years_of_experience: string;
  highest_education: string;
  skills: string;
  certifications: string;
  languages: string;
  awards: string;
  self_evaluation: string;
};

type HighlightRange = {
  start: number;
  end: number;
  tone: "active" | "keyword" | "source";
};

type AppliedEvidence = {
  value: string;
  candidateId: string;
  extractor: string;
  confidence: number | null;
  sourceText: string | null;
};

const fieldLabels: Record<keyof EditableForm, string> = {
  name: "姓名",
  phone: "手机号",
  email: "邮箱",
  city: "城市",
  current_company: "当前公司",
  current_title: "当前岗位",
  years_of_experience: "工作年限",
  highest_education: "最高学历",
  skills: "技能关键词",
  certifications: "证书",
  languages: "语言能力",
  awards: "奖项荣誉",
  self_evaluation: "自我评价",
};

const singleLineFields: Array<keyof EditableForm> = [
  "name",
  "phone",
  "email",
  "city",
  "current_company",
  "current_title",
  "years_of_experience",
  "highest_education",
];

const multiLineFields: Array<keyof EditableForm> = [
  "skills",
  "certifications",
  "languages",
  "awards",
  "self_evaluation",
];

function toForm(data: CandidateReviewData): EditableForm {
  const candidate = data.candidate;
  return {
    name: candidate.name ?? "",
    phone: candidate.phone ?? "",
    email: candidate.email ?? "",
    city: candidate.city ?? "",
    current_company: candidate.current_company ?? "",
    current_title: candidate.current_title ?? "",
    years_of_experience:
      candidate.years_of_experience === null ? "" : String(candidate.years_of_experience),
    highest_education: candidate.highest_education ?? "",
    skills: candidate.skills.join("\n"),
    certifications: candidate.certifications.join("\n"),
    languages: candidate.languages.join("\n"),
    awards: candidate.awards.join("\n"),
    self_evaluation: candidate.self_evaluation ?? "",
  };
}

export default function CandidateReviewPage() {
  const params = useParams<{ jobId: string; candidateId: string }>();
  const [data, setData] = useState<CandidateReviewData | null>(null);
  const [form, setForm] = useState<EditableForm | null>(null);
  const [parseRun, setParseRun] = useState<ResumeParseRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [matching, setMatching] = useState(false);
  const [match, setMatch] = useState<CandidateMatch | null>(null);
  const [activeField, setActiveField] = useState<keyof EditableForm | null>(null);
  const [activeEvidenceText, setActiveEvidenceText] = useState<string | null>(null);
  const [appliedEvidence, setAppliedEvidence] = useState<Partial<Record<keyof EditableForm, AppliedEvidence>>>({});
  const previewRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const reviewData = await getCandidateReviewData(params.jobId, params.candidateId);
      setData(reviewData);
      setForm(toForm(reviewData));
      try {
        setParseRun(await getLatestResumeParseRun(reviewData.resume_file.id));
      } catch {
        setParseRun(null);
      }
      try {
        setMatch(await getCandidateMatch(params.jobId, params.candidateId));
      } catch {
        setMatch(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "修正数据加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, [params.jobId, params.candidateId]);

  function setField(key: keyof EditableForm, value: string) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
    setAppliedEvidence((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  }

  function applyCandidate(fieldName: keyof EditableForm, candidate: ResumeFieldCandidate) {
    const value = candidateValueForForm(candidate.value_json);
    setForm((current) => (current ? { ...current, [fieldName]: value } : current));
    setAppliedEvidence((current) => ({
      ...current,
      [fieldName]: {
        value,
        candidateId: candidate.id,
        extractor: candidate.extractor,
        confidence: candidate.confidence,
        sourceText: candidate.source_text,
      },
    }));
    setActiveField(fieldName);
    setActiveEvidenceText(candidate.source_text);
    window.setTimeout(() => {
      previewRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 0);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form) return;
    const years = form.years_of_experience.trim();
    if (years && Number.isNaN(Number(years))) {
      setError("工作年限必须是数字");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await updateCandidate(params.candidateId, {
        name: form.name || null,
        phone: form.phone || null,
        email: form.email || null,
        city: form.city || null,
        current_company: form.current_company || null,
        current_title: form.current_title || null,
        years_of_experience: years ? Number(years) : null,
        highest_education: form.highest_education || null,
        skills: splitLines(form.skills),
        certifications: splitLines(form.certifications),
        languages: splitLines(form.languages),
        awards: splitLines(form.awards),
        self_evaluation: form.self_evaluation || null,
        correction_sources: correctionSourcesForSubmit(form, appliedEvidence),
      });
      setMessage("修正已保存；vNext 候选来源已写入修改记录。");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleRematch() {
    setMatching(true);
    setError(null);
    setMessage(null);
    try {
      setMatch(await createCandidateMatch(params.jobId, params.candidateId));
      setMessage("匹配评分已更新");
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新评分失败");
    } finally {
      setMatching(false);
    }
  }

  function locateField(fieldName: keyof EditableForm, sourceText?: string | null) {
    setActiveField(fieldName);
    setActiveEvidenceText(sourceText || null);
    window.setTimeout(() => {
      previewRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 0);
  }

  const candidatesByField = useMemo(() => groupFieldCandidates(parseRun), [parseRun]);
  const lowConfidenceFields = useMemo(
    () => new Set(data?.candidate.low_confidence_fields ?? []),
    [data?.candidate.low_confidence_fields],
  );

  const highlightRanges = useMemo(() => {
    if (!data) return [];
    const content = data.preview.content;
    const ranges: HighlightRange[] = [];
    for (const extraction of data.field_extractions) {
      const range = resolveExtractionRange(content, extraction);
      if (!range) continue;
      ranges.push({
        ...range,
        tone: extraction.field_name === activeField ? "active" : "source",
      });
    }
    if (activeEvidenceText) {
      for (const range of findAllRanges(content, activeEvidenceText)) {
        ranges.push({ ...range, tone: "active" });
      }
    }
    for (const skill of data.candidate.skills) {
      for (const range of findAllRanges(content, skill)) {
        ranges.push({ ...range, tone: "keyword" });
      }
    }
    return ranges;
  }, [activeEvidenceText, activeField, data]);

  return (
    <WorkspaceShell
      title="解析结果修正"
      description="左侧修正结构化字段，右侧对照原简历抽取文本。保存后可重新触发匹配评分。"
      backHref={`/jobs/${params.jobId}/candidates/${params.candidateId}`}
      backLabel="返回候选人详情"
      actions={
        <>
          <button type="button" onClick={() => void handleRematch()} disabled={matching || !data} className="btn-secondary">
            {matching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            重新评分
          </button>
          <button type="submit" form="candidate-review-form" disabled={saving || !form} className="btn-primary">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            保存修正
          </button>
        </>
      }
    >
      {error ? <Notice tone="error">{error}</Notice> : null}
      {message ? <Notice tone="success">{message}</Notice> : null}

      {loading || !data || !form ? (
        <div className="panel flex items-center gap-2 p-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          正在加载修正数据
        </div>
      ) : (
        <div className="grid gap-5 xl:grid-cols-[minmax(460px,560px)_minmax(0,1fr)]">
          <form id="candidate-review-form" onSubmit={handleSubmit} className="panel overflow-hidden">
            <div className="border-b border-border bg-slate-50/80 px-5 py-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold">结构化字段</h2>
                  <p className="mt-1 text-sm text-muted-foreground">低置信字段优先显示 vNext 候选证据。</p>
                </div>
                <ParseRunBadge parseRun={parseRun} />
              </div>
            </div>
            <div className="divide-y divide-border">
              {orderFieldsByConfidence(singleLineFields, lowConfidenceFields).map((fieldName) => (
                <ReviewFieldRow
                  key={fieldName}
                  fieldName={fieldName}
                  value={form[fieldName]}
                  multiline={false}
                  candidates={candidatesByField[fieldName] ?? []}
                  lowConfidence={lowConfidenceFields.has(fieldName)}
                  appliedEvidence={appliedEvidence[fieldName]}
                  onChange={(value) => setField(fieldName, value)}
                  onLocate={(sourceText) => locateField(fieldName, sourceText)}
                  onApply={(candidate) => applyCandidate(fieldName, candidate)}
                />
              ))}
              {orderFieldsByConfidence(multiLineFields, lowConfidenceFields).map((fieldName) => (
                <ReviewFieldRow
                  key={fieldName}
                  fieldName={fieldName}
                  value={form[fieldName]}
                  multiline
                  candidates={candidatesByField[fieldName] ?? []}
                  lowConfidence={lowConfidenceFields.has(fieldName)}
                  appliedEvidence={appliedEvidence[fieldName]}
                  onChange={(value) => setField(fieldName, value)}
                  onLocate={(sourceText) => locateField(fieldName, sourceText)}
                  onApply={(candidate) => applyCandidate(fieldName, candidate)}
                />
              ))}
            </div>

            <div className="m-5 rounded-md bg-muted p-4">
              <h3 className="text-sm font-semibold">待确认字段</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {data.candidate.low_confidence_fields.length
                  ? data.candidate.low_confidence_fields.map((field) => fieldLabels[field as keyof EditableForm] ?? field).join("、")
                  : "暂无"}
              </p>
            </div>
          </form>

          <section className="space-y-5">
            <div className="panel p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-semibold">匹配评分</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {match ? `${match.score} 分 / ${match.level}` : "暂无评分"}
                  </p>
                </div>
                <button type="button" onClick={() => void handleRematch()} disabled={matching} className="btn-secondary">
                  {matching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  重新评分
                </button>
              </div>
              {match ? <p className="mt-3 text-sm leading-6 text-muted-foreground">{match.summary}</p> : null}
            </div>

            <div className="panel p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-semibold">原简历预览</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{data.resume_file.file_name}</p>
                </div>
                <span className="status-pill">
                  {data.resume_file.parse_status === "success" ? "解析成功" : "解析失败"}
                </span>
              </div>
              {activeField ? (
                <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                  当前定位：{fieldLabels[activeField]}
                  {activeEvidenceText ? <span className="ml-2">已高亮 vNext 证据</span> : null}
                </div>
              ) : null}
              <div
                ref={previewRef}
                className="mt-4 max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md bg-muted p-4 text-sm leading-7 text-foreground"
              >
                {renderHighlightedText(data.preview.content, highlightRanges)}
              </div>
            </div>

            <div className="panel p-5">
              <h3 className="text-base font-semibold">修改记录</h3>
              {data.correction_logs.length ? (
                <div className="mt-3 space-y-2">
                  {data.correction_logs.slice(0, 8).map((log) => (
                    <div key={log.id} className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                      {log.field_name}: {log.old_value || "空"} {"->"} {log.new_value || "空"}
                      <CorrectionSourceBadge editorId={log.editor_id} />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">暂无修改记录</p>
              )}
            </div>
          </section>
        </div>
      )}
    </WorkspaceShell>
  );
}

function ParseRunBadge({ parseRun }: { parseRun: ResumeParseRun | null }) {
  if (!parseRun) {
    return <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">无 vNext 证据</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
      <FileSearch className="h-3.5 w-3.5" />
      vNext {Math.round(parseRun.quality_score ?? 0)}%
    </span>
  );
}

function ReviewFieldRow({
  fieldName,
  value,
  multiline,
  candidates,
  lowConfidence,
  appliedEvidence,
  onChange,
  onLocate,
  onApply,
}: {
  fieldName: keyof EditableForm;
  value: string;
  multiline: boolean;
  candidates: ResumeFieldCandidate[];
  lowConfidence: boolean;
  appliedEvidence?: AppliedEvidence;
  onChange: (value: string) => void;
  onLocate: (sourceText?: string | null) => void;
  onApply: (candidate: ResumeFieldCandidate) => void;
}) {
  const sortedCandidates = sortFieldCandidates(candidates);
  return (
    <div className={lowConfidence ? "bg-amber-50/50 px-5 py-4" : "px-5 py-4"}>
      <div className="flex items-start justify-between gap-3">
        <label className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2 text-sm font-medium">
            {fieldLabels[fieldName]}
            {lowConfidence ? <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">低置信</span> : null}
            {appliedEvidence ? (
              <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                <CheckCircle2 className="h-3 w-3" />
                来自 vNext 候选
              </span>
            ) : null}
          </span>
          {multiline ? (
            <textarea
              className="input mt-2 min-h-24 resize-y"
              value={value}
              onChange={(event) => onChange(event.target.value)}
            />
          ) : (
            <input className="input mt-2" value={value} onChange={(event) => onChange(event.target.value)} />
          )}
        </label>
        <button type="button" onClick={() => onLocate()} className="mt-7 text-xs font-semibold text-primary">
          定位
        </button>
      </div>
      {appliedEvidence ? (
        <p className="mt-2 text-xs text-emerald-700">
          已套用：{appliedEvidence.extractor} / 置信度 {formatConfidence(appliedEvidence.confidence)}
        </p>
      ) : null}
      <FieldCandidateList candidates={sortedCandidates} onLocate={onLocate} onApply={onApply} />
    </div>
  );
}

function FieldCandidateList({
  candidates,
  onLocate,
  onApply,
}: {
  candidates: ResumeFieldCandidate[];
  onLocate: (sourceText?: string | null) => void;
  onApply: (candidate: ResumeFieldCandidate) => void;
}) {
  if (!candidates.length) {
    return <p className="mt-2 text-xs text-muted-foreground">暂无 vNext 候选，保留旧字段修正体验。</p>;
  }
  return (
    <div className="mt-3 space-y-2">
      {candidates.slice(0, 4).map((candidate) => (
        <div key={candidate.id} className="rounded-md border border-border bg-white px-3 py-2">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => onApply(candidate)}
                  className="line-clamp-2 text-left text-sm font-medium text-primary hover:underline"
                >
                  {candidateValueForDisplay(candidate.value_json) || "空值"}
                </button>
                <span className={candidate.selected ? "rounded bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700" : "rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600"}>
                  {candidate.selected ? "已采用" : "未采用"}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {candidate.extractor} / 置信度 {formatConfidence(candidate.confidence)}
              </p>
            </div>
            <button type="button" onClick={() => onApply(candidate)} className="btn-secondary h-8 shrink-0 text-xs">
              套用
            </button>
          </div>
          {candidate.source_text ? (
            <div className="mt-2 rounded-md bg-slate-50 px-2 py-2">
              <p className="line-clamp-2 text-xs leading-5 text-muted-foreground">{candidate.source_text}</p>
              <button type="button" onClick={() => onLocate(candidate.source_text)} className="mt-1 text-xs font-semibold text-primary">
                定位证据
              </button>
            </div>
          ) : null}
          {candidate.rejection_reason ? <p className="mt-2 text-xs text-amber-700">原因：{candidate.rejection_reason}</p> : null}
        </div>
      ))}
    </div>
  );
}

function correctionSourcesForSubmit(
  form: EditableForm,
  appliedEvidence: Partial<Record<keyof EditableForm, AppliedEvidence>>,
) {
  const sources: Record<string, { candidate_id: string; extractor: string; confidence: number | null; source_text: string | null }> = {};
  for (const [fieldName, evidence] of Object.entries(appliedEvidence) as Array<[keyof EditableForm, AppliedEvidence]>) {
    if (!evidence || form[fieldName] !== evidence.value) continue;
    sources[fieldName] = {
      candidate_id: evidence.candidateId,
      extractor: evidence.extractor,
      confidence: evidence.confidence,
      source_text: evidence.sourceText,
    };
  }
  return sources;
}

function CorrectionSourceBadge({ editorId }: { editorId: string | null }) {
  if (!editorId?.startsWith("vnext:")) return null;
  const source = editorId.replace(/^vnext:/, "");
  return <span className="ml-2 rounded bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">来自 vNext 候选 {source}</span>;
}

function splitLines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function groupFieldCandidates(parseRun: ResumeParseRun | null): Partial<Record<keyof EditableForm, ResumeFieldCandidate[]>> {
  if (!parseRun) return {};
  const groups: Partial<Record<keyof EditableForm, ResumeFieldCandidate[]>> = {};
  for (const candidate of parseRun.field_candidates) {
    if (!isEditableField(candidate.field_name)) continue;
    groups[candidate.field_name] = [...(groups[candidate.field_name] ?? []), candidate];
  }
  return groups;
}

function isEditableField(fieldName: string): fieldName is keyof EditableForm {
  return fieldName in fieldLabels;
}

function sortFieldCandidates(candidates: ResumeFieldCandidate[]) {
  return [...candidates].sort((a, b) => {
    const selectedDelta = Number(b.selected) - Number(a.selected);
    if (selectedDelta) return selectedDelta;
    return (b.confidence ?? -1) - (a.confidence ?? -1);
  });
}

function orderFieldsByConfidence<T extends keyof EditableForm>(fields: T[], lowConfidenceFields: Set<string>) {
  return [...fields].sort((a, b) => Number(lowConfidenceFields.has(b)) - Number(lowConfidenceFields.has(a)));
}

function candidateValueForForm(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map((item) => candidateValueForForm(item)).filter(Boolean).join("\n");
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const preferred = ["raw", "name", "company", "school", "title", "degree", "description"];
    const parts = preferred.map((key) => record[key]).filter((item) => typeof item === "string" && item.trim()).map(String);
    return parts.length ? parts.join(" / ") : JSON.stringify(value);
  }
  return "";
}

function candidateValueForDisplay(value: unknown): string {
  const text = candidateValueForForm(value);
  return text.replace(/\n+/g, "、");
}

function formatConfidence(value: number | null | undefined) {
  return value === null || value === undefined ? "-" : `${Math.round(value * 100)}%`;
}

function resolveExtractionRange(
  content: string,
  extraction: CandidateReviewData["field_extractions"][number],
): { start: number; end: number } | null {
  if (
    typeof extraction.text_start_offset === "number" &&
    typeof extraction.text_end_offset === "number" &&
    extraction.text_end_offset > extraction.text_start_offset
  ) {
    return { start: extraction.text_start_offset, end: extraction.text_end_offset };
  }
  const needle = extraction.source_text || extraction.extracted_value;
  if (!needle) return null;
  const start = content.indexOf(needle);
  return start >= 0 ? { start, end: start + needle.length } : null;
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

function renderHighlightedText(content: string, ranges: HighlightRange[]): ReactNode[] {
  const merged = mergeRanges(ranges, content.length);
  const nodes: ReactNode[] = [];
  let cursor = 0;
  for (const range of merged) {
    if (range.start > cursor) {
      nodes.push(content.slice(cursor, range.start));
    }
    nodes.push(
      <mark key={`${range.start}-${range.end}-${range.tone}`} className={highlightClass(range.tone)}>
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

function mergeRanges(ranges: HighlightRange[], maxLength: number): HighlightRange[] {
  const priority = { active: 3, source: 2, keyword: 1 };
  const normalized = ranges
    .map((range) => ({
      ...range,
      start: Math.max(0, Math.min(maxLength, range.start)),
      end: Math.max(0, Math.min(maxLength, range.end)),
    }))
    .filter((range) => range.end > range.start)
    .sort((a, b) => a.start - b.start || priority[b.tone] - priority[a.tone]);

  const result: HighlightRange[] = [];
  for (const range of normalized) {
    const previous = result[result.length - 1];
    if (!previous || range.start >= previous.end) {
      result.push(range);
      continue;
    }
    if (priority[range.tone] > priority[previous.tone]) {
      previous.end = range.start;
      if (previous.end <= previous.start) result.pop();
      result.push(range);
    }
  }
  return result;
}

function highlightClass(tone: HighlightRange["tone"]) {
  if (tone === "active") return "rounded-sm bg-amber-200 px-0.5 text-amber-950";
  if (tone === "source") return "rounded-sm bg-sky-100 px-0.5 text-sky-950";
  return "rounded-sm bg-emerald-100 px-0.5 text-emerald-950";
}
