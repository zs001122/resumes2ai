"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import type { ReactNode } from "react";
import { Loader2, Save, Wand2 } from "lucide-react";

import { Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import { createJob, JDParseResult, parseJD } from "@/lib/api";

const emptyParseResult: JDParseResult = {
  responsibilities: [],
  must_have: [],
  nice_to_have: [],
  deal_breakers: [],
  scoring_dimensions: [],
};

function linesToList(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(value: string[]) {
  return value.join("\n");
}

export default function NewJobPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    department: "",
    location: "",
    salary_range: "",
    experience_required: "",
    education_required: "",
    jd: "",
  });
  const [standards, setStandards] = useState(emptyParseResult);
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateForm(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateStandard(key: keyof JDParseResult, value: string) {
    setStandards((current) => ({ ...current, [key]: linesToList(value) }));
  }

  async function handleParse() {
    setError(null);
    if (!form.jd.trim()) {
      setError("请先填写岗位 JD");
      return;
    }
    setParsing(true);
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
    setError(null);
    if (!form.title.trim() || !form.jd.trim()) {
      setError("岗位名称和 JD 必填");
      return;
    }
    setSaving(true);
    try {
      const created = await createJob({
        title: form.title,
        department: form.department || null,
        location: form.location || null,
        salary_range: form.salary_range || null,
        experience_required: form.experience_required || null,
        education_required: form.education_required || null,
        jd: form.jd,
        ...standards,
      });
      router.push(`/jobs/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "岗位保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <WorkspaceShell
      title="创建岗位"
      description="先录入岗位基础信息和 JD，再由系统生成筛选标准，保存前可以人工修正。"
      backHref="/jobs"
      backLabel="返回岗位列表"
      actions={
        <button type="submit" form="job-form" disabled={saving} className="btn-primary">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          保存岗位
        </button>
      }
    >
      {error ? <Notice tone="error">{error}</Notice> : null}

      <form id="job-form" onSubmit={handleSubmit} className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
        <section className="panel p-5">
          <div className="border-b border-border pb-4">
            <h2 className="text-base font-semibold">岗位信息</h2>
            <p className="mt-1 text-sm text-muted-foreground">这些字段会影响候选人匹配评分和列表筛选。</p>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <Field label="岗位名称" required>
              <input className="input" value={form.title} onChange={(e) => updateForm("title", e.target.value)} />
            </Field>
            <Field label="所属部门">
              <input className="input" value={form.department} onChange={(e) => updateForm("department", e.target.value)} />
            </Field>
            <Field label="工作地点">
              <input className="input" value={form.location} onChange={(e) => updateForm("location", e.target.value)} />
            </Field>
            <Field label="薪资范围">
              <input className="input" value={form.salary_range} onChange={(e) => updateForm("salary_range", e.target.value)} />
            </Field>
            <Field label="年限要求">
              <input className="input" value={form.experience_required} onChange={(e) => updateForm("experience_required", e.target.value)} />
            </Field>
            <Field label="学历要求">
              <input className="input" value={form.education_required} onChange={(e) => updateForm("education_required", e.target.value)} />
            </Field>
          </div>
          <Field label="岗位 JD" required className="mt-4">
            <textarea
              className="input min-h-72 resize-y"
              value={form.jd}
              onChange={(e) => updateForm("jd", e.target.value)}
            />
          </Field>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={() => void handleParse()} disabled={parsing} className="btn-secondary">
              {parsing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
              解析 JD
            </button>
            <Link href="/jobs" className="btn-secondary">
              取消
            </Link>
          </div>
        </section>

        <section className="panel p-5">
          <div className="border-b border-border pb-4">
            <h2 className="text-base font-semibold">筛选标准</h2>
            <p className="mt-1 text-sm text-muted-foreground">每行一条，建议保留少量高价值条件。</p>
          </div>
          <StandardTextarea label="岗位职责" value={standards.responsibilities} onChange={(v) => updateStandard("responsibilities", v)} />
          <StandardTextarea label="必备条件" value={standards.must_have} onChange={(v) => updateStandard("must_have", v)} />
          <StandardTextarea label="加分条件" value={standards.nice_to_have} onChange={(v) => updateStandard("nice_to_have", v)} />
          <StandardTextarea label="排除条件" value={standards.deal_breakers} onChange={(v) => updateStandard("deal_breakers", v)} />
          <StandardTextarea label="评分维度" value={standards.scoring_dimensions} onChange={(v) => updateStandard("scoring_dimensions", v)} />
        </section>
      </form>
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
}: {
  label: string;
  value: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="mt-4 block">
      <span className="text-sm font-medium">{label}</span>
      <textarea
        className="input mt-2 min-h-20 resize-y"
        value={listToLines(value)}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
