"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { AlertTriangle, Loader2, Save, Wand2 } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import { JDParseResult, Job, getJob, parseJD, updateJob } from "@/lib/api";

function linesToList(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(value: string[]) {
  return value.join("\n");
}

const emptyStandards: JDParseResult = {
  responsibilities: [],
  must_have: [],
  nice_to_have: [],
  deal_breakers: [],
  scoring_dimensions: [],
};

export default function EditJobPage() {
  const params = useParams<{ jobId: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [form, setForm] = useState({
    title: "",
    department: "",
    location: "",
    salary_range: "",
    experience_required: "",
    education_required: "",
    jd: "",
  });
  const [standards, setStandards] = useState<JDParseResult>(emptyStandards);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadJob() {
      setLoading(true);
      setError(null);
      try {
        const loaded = await getJob(params.jobId);
        setJob(loaded);
        setForm({
          title: loaded.title,
          department: loaded.department ?? "",
          location: loaded.location ?? "",
          salary_range: loaded.salary_range ?? "",
          experience_required: loaded.experience_required ?? "",
          education_required: loaded.education_required ?? "",
          jd: loaded.jd,
        });
        setStandards({
          responsibilities: loaded.responsibilities,
          must_have: loaded.must_have,
          nice_to_have: loaded.nice_to_have,
          deal_breakers: loaded.deal_breakers,
          scoring_dimensions: loaded.scoring_dimensions,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "岗位加载失败");
      } finally {
        setLoading(false);
      }
    }
    void loadJob();
  }, [params.jobId]);

  function updateForm(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateStandard(key: keyof JDParseResult, value: string) {
    setStandards((current) => ({ ...current, [key]: linesToList(value) }));
  }

  async function handleParse() {
    if (!form.jd.trim()) {
      setError("请先填写岗位 JD");
      return;
    }
    setParsing(true);
    setError(null);
    try {
      setStandards(
        await parseJD({
          title: form.title || undefined,
          jd: form.jd,
          experience_required: form.experience_required || undefined,
          education_required: form.education_required || undefined,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "JD 解析失败");
    } finally {
      setParsing(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim() || !form.jd.trim()) {
      setError("岗位名称和 JD 必填");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateJob(params.jobId, {
        title: form.title,
        department: form.department || null,
        location: form.location || null,
        salary_range: form.salary_range || null,
        experience_required: form.experience_required || null,
        education_required: form.education_required || null,
        jd: form.jd,
        ...standards,
      });
      router.push(`/jobs/${params.jobId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "岗位保存失败");
    } finally {
      setSaving(false);
    }
  }

  const isClosed = job?.status === "closed";

  return (
    <WorkspaceShell
      title="编辑岗位"
      description="调整岗位信息和筛选标准。标准字段变更后会生成新版本，并建议对历史候选人重新评分。"
      backHref={`/jobs/${params.jobId}`}
      backLabel="返回岗位详情"
      actions={
        !isClosed ? (
          <button type="submit" form="job-edit-form" disabled={saving || loading} className="btn-primary">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            保存修改
          </button>
        ) : null
      }
    >
      {error ? <Notice tone="error">{error}</Notice> : null}
      {isClosed ? (
        <Notice tone="info">
          已关闭岗位不能直接编辑。请复制岗位后再修改新岗位的 JD 和筛选标准。
        </Notice>
      ) : null}

      {loading ? (
        <div className="panel flex items-center gap-2 p-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          正在加载岗位
        </div>
      ) : (
        <form id="job-edit-form" onSubmit={handleSubmit} className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
          <section className="panel p-5">
            <div className="border-b border-border pb-4">
              <h2 className="text-base font-semibold">岗位信息</h2>
              <p className="mt-1 text-sm text-muted-foreground">基础字段用于岗位展示和候选人列表上下文。</p>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <Field label="岗位名称" required>
                <input disabled={isClosed} className="input" value={form.title} onChange={(e) => updateForm("title", e.target.value)} />
              </Field>
              <Field label="所属部门">
                <input disabled={isClosed} className="input" value={form.department} onChange={(e) => updateForm("department", e.target.value)} />
              </Field>
              <Field label="工作地点">
                <input disabled={isClosed} className="input" value={form.location} onChange={(e) => updateForm("location", e.target.value)} />
              </Field>
              <Field label="薪资范围">
                <input disabled={isClosed} className="input" value={form.salary_range} onChange={(e) => updateForm("salary_range", e.target.value)} />
              </Field>
              <Field label="年限要求">
                <input disabled={isClosed} className="input" value={form.experience_required} onChange={(e) => updateForm("experience_required", e.target.value)} />
              </Field>
              <Field label="学历要求">
                <input disabled={isClosed} className="input" value={form.education_required} onChange={(e) => updateForm("education_required", e.target.value)} />
              </Field>
            </div>
            <Field label="岗位 JD" required className="mt-4">
              <textarea disabled={isClosed} className="input min-h-72 resize-y" value={form.jd} onChange={(e) => updateForm("jd", e.target.value)} />
            </Field>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" onClick={() => void handleParse()} disabled={parsing || isClosed} className="btn-secondary">
                {parsing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                重新解析 JD
              </button>
              <Link href={`/jobs/${params.jobId}`} className="btn-secondary">
                取消
              </Link>
            </div>
          </section>

          <section className="panel p-5">
            <div className="border-b border-border pb-4">
              <h2 className="text-base font-semibold">筛选标准</h2>
              <div className="mt-3 flex items-start gap-2 rounded-md bg-amber-50 px-3 py-3 text-sm text-amber-800">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>修改这些字段会生成新的岗位标准版本，保存后建议对历史候选人重新评分。</p>
              </div>
            </div>
            <StandardTextarea disabled={isClosed} label="岗位职责" value={standards.responsibilities} onChange={(v) => updateStandard("responsibilities", v)} />
            <StandardTextarea disabled={isClosed} label="必备条件" value={standards.must_have} onChange={(v) => updateStandard("must_have", v)} />
            <StandardTextarea disabled={isClosed} label="加分条件" value={standards.nice_to_have} onChange={(v) => updateStandard("nice_to_have", v)} />
            <StandardTextarea disabled={isClosed} label="排除条件" value={standards.deal_breakers} onChange={(v) => updateStandard("deal_breakers", v)} />
            <StandardTextarea disabled={isClosed} label="评分维度" value={standards.scoring_dimensions} onChange={(v) => updateStandard("scoring_dimensions", v)} />
          </section>
        </form>
      )}
    </WorkspaceShell>
  );
}

function Field({
  label,
  required,
  className,
  children,
}: {
  label: string;
  required?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <label className={`block ${className ?? ""}`}>
      <span className="text-sm font-medium">
        {label}
        {required ? <span className="text-red-600"> *</span> : null}
      </span>
      <div className="mt-2">{children}</div>
    </label>
  );
}

function StandardTextarea({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: string[];
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="mt-4 block">
      <span className="text-sm font-medium">{label}</span>
      <textarea
        disabled={disabled}
        className="input mt-2 min-h-20 resize-y"
        value={listToLines(value)}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
