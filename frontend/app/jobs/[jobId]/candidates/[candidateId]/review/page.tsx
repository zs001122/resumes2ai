"use client";

import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Loader2, RefreshCw, Save } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  CandidateMatch,
  CandidateReviewData,
  createCandidateMatch,
  getCandidateMatch,
  getCandidateReviewData,
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
};

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
  };
}

export default function CandidateReviewPage() {
  const params = useParams<{ jobId: string; candidateId: string }>();
  const [data, setData] = useState<CandidateReviewData | null>(null);
  const [form, setForm] = useState<EditableForm | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [matching, setMatching] = useState(false);
  const [match, setMatch] = useState<CandidateMatch | null>(null);
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
        skills: form.skills
          .split("\n")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setMessage("修正已保存");
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
        <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
          <form id="candidate-review-form" onSubmit={handleSubmit} className="panel p-5">
            <div className="border-b border-border pb-4">
              <h2 className="text-base font-semibold">结构化字段</h2>
              <p className="mt-1 text-sm text-muted-foreground">关键字段会影响候选人列表和匹配评分。</p>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              <Field label="姓名" value={form.name} onChange={(v) => setField("name", v)} />
              <Field label="手机号" value={form.phone} onChange={(v) => setField("phone", v)} />
              <Field label="邮箱" value={form.email} onChange={(v) => setField("email", v)} />
              <Field label="城市" value={form.city} onChange={(v) => setField("city", v)} />
              <Field label="当前公司" value={form.current_company} onChange={(v) => setField("current_company", v)} />
              <Field label="当前岗位" value={form.current_title} onChange={(v) => setField("current_title", v)} />
              <Field label="工作年限" value={form.years_of_experience} onChange={(v) => setField("years_of_experience", v)} />
              <Field label="最高学历" value={form.highest_education} onChange={(v) => setField("highest_education", v)} />
            </div>

            <label className="mt-4 block">
              <span className="text-sm font-medium">技能关键词</span>
              <textarea
                className="input mt-2 min-h-28 resize-y"
                value={form.skills}
                onChange={(event) => setField("skills", event.target.value)}
              />
            </label>

            <div className="mt-5 rounded-md bg-muted p-4">
              <h3 className="text-sm font-semibold">待确认字段</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {data.candidate.low_confidence_fields.length
                  ? data.candidate.low_confidence_fields.join("、")
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
              <pre className="mt-4 max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md bg-muted p-4 text-sm leading-7 text-foreground">
                {data.preview.content}
              </pre>
            </div>

            <div className="panel p-5">
              <h3 className="text-base font-semibold">修改记录</h3>
              {data.correction_logs.length ? (
                <div className="mt-3 space-y-2">
                  {data.correction_logs.slice(0, 8).map((log) => (
                    <div key={log.id} className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                      {log.field_name}: {log.old_value || "空"} {"->"} {log.new_value || "空"}
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

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      <input className="input mt-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}
