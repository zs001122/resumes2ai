"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Loader2, RefreshCw, Upload } from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  CandidateListItem,
  CandidateStatusValue,
  bulkAddCandidatesToTalentPool,
  bulkUpdateCandidateStatus,
  listCandidates,
  rematchJobCandidates,
  updateCandidateStatus,
} from "@/lib/api";

const statusOptions: Array<{ value: CandidateStatusValue; label: string }> = [
  { value: "pending", label: "待筛选" },
  { value: "favorite", label: "已收藏" },
  { value: "pending_contact", label: "待沟通" },
  { value: "rejected", label: "已淘汰" },
  { value: "archived", label: "已入库" },
];

const levelOptions = ["强推荐", "可沟通", "可考虑", "备选", "谨慎", "不推荐"];

export default function CandidatesPage() {
  const params = useParams<{ jobId: string }>();
  const [items, setItems] = useState<CandidateListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [minScore, setMinScore] = useState("");
  const [maxScore, setMaxScore] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [skillFilter, setSkillFilter] = useState("");
  const [educationFilter, setEducationFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [lowConfidenceFilter, setLowConfidenceFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusSavingId, setStatusSavingId] = useState<string | null>(null);
  const [bulkSaving, setBulkSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bulkResult, setBulkResult] = useState<string | null>(null);

  async function loadCandidates() {
    setLoading(true);
    setError(null);
    try {
      setItems(
        await listCandidates(params.jobId, {
          status: statusFilter,
          level: levelFilter,
          min_score: minScore,
          max_score: maxScore,
          city: cityFilter,
          skill: skillFilter,
          education: educationFilter,
          has_risk: riskFilter,
          low_confidence: lowConfidenceFilter,
        }),
      );
      setSelectedIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选人列表加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function runBulkStatus(value: CandidateStatusValue) {
    if (!selectedIds.length) return;
    const requestedCount = selectedIds.length;
    setBulkSaving(true);
    setError(null);
    setBulkResult(null);
    try {
      const result = await bulkUpdateCandidateStatus(params.jobId, selectedIds, value);
      await loadCandidates();
      setBulkResult(formatBulkResult("批量状态更新", requestedCount, result.length));
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量更新失败");
    } finally {
      setBulkSaving(false);
    }
  }

  async function runBulkArchive() {
    if (!selectedIds.length) return;
    const requestedCount = selectedIds.length;
    setBulkSaving(true);
    setError(null);
    setBulkResult(null);
    try {
      const result = await bulkAddCandidatesToTalentPool(params.jobId, selectedIds);
      await loadCandidates();
      setBulkResult(formatBulkResult("批量加入人才库", requestedCount, result.length));
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量入库失败");
    } finally {
      setBulkSaving(false);
    }
  }

  async function runBulkMatch() {
    if (!selectedIds.length) return;
    const requestedCount = selectedIds.length;
    setBulkSaving(true);
    setError(null);
    setBulkResult(null);
    try {
      const result = await rematchJobCandidates(params.jobId, selectedIds);
      await loadCandidates();
      setBulkResult(formatBulkResult("批量重新评分", requestedCount, result.succeeded));
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量重新评分失败");
    } finally {
      setBulkSaving(false);
    }
  }

  function toggleCandidate(candidateId: string) {
    setSelectedIds((current) =>
      current.includes(candidateId) ? current.filter((id) => id !== candidateId) : [...current, candidateId],
    );
  }

  async function changeStatus(candidateId: string, value: CandidateStatusValue) {
    setStatusSavingId(candidateId);
    setError(null);
    try {
      await updateCandidateStatus(params.jobId, candidateId, value);
      await loadCandidates();
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选人状态更新失败");
    } finally {
      setStatusSavingId(null);
    }
  }

  useEffect(() => {
    void loadCandidates();
  }, [params.jobId]);

  const sorted = [...items].sort((a, b) => (b.match?.score ?? -1) - (a.match?.score ?? -1));
  const allVisibleSelected = sorted.length > 0 && sorted.every((item) => selectedIds.includes(item.candidate.id));
  const stats = useMemo(
    () => ({
      total: items.length,
      high: items.filter((item) => (item.match?.score ?? 0) >= 85).length,
      pending: items.filter((item) => !item.status || item.status.status === "pending").length,
    }),
    [items],
  );

  return (
    <WorkspaceShell
      title="候选人筛选"
      description="按岗位匹配分排序，结合状态筛选快速推进初筛决策。"
      backHref={`/jobs/${params.jobId}`}
      backLabel="返回岗位详情"
      actions={
        <>
          <Link href={`/jobs/${params.jobId}/resumes/upload`} className="btn-primary">
            <Upload className="h-4 w-4" />
            上传简历
          </Link>
          <button onClick={() => void loadCandidates()} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新
          </button>
        </>
      }
    >
      {error ? (
        <Notice
          tone="error"
          action={
            <button onClick={() => void loadCandidates()} className="btn-secondary h-8 text-xs">
              重试
            </button>
          }
        >
          {error}
        </Notice>
      ) : null}
      {bulkResult ? <Notice tone="success">{bulkResult}</Notice> : null}

      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <Stat label="候选人" value={stats.total} />
        <Stat label="强匹配" value={stats.high} />
        <Stat label="待筛选" value={stats.pending} />
      </div>

      <section className="panel mb-5 p-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-[1fr_1fr_1fr_1fr_1fr_auto]">
          <select className="input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">全部状态</option>
            {statusOptions.map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
          <select className="input" value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
            <option value="">全部推荐等级</option>
            {levelOptions.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
          <input
            className="input"
            inputMode="numeric"
            placeholder="最低匹配分"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value.replace(/[^\d.]/g, ""))}
          />
          <input
            className="input"
            inputMode="numeric"
            placeholder="最高匹配分"
            value={maxScore}
            onChange={(e) => setMaxScore(e.target.value.replace(/[^\d.]/g, ""))}
          />
          <input className="input" placeholder="城市" value={cityFilter} onChange={(e) => setCityFilter(e.target.value)} />
          <button onClick={() => void loadCandidates()} className="btn-primary">
            应用筛选
          </button>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <input className="input" placeholder="技能关键词" value={skillFilter} onChange={(e) => setSkillFilter(e.target.value)} />
          <input className="input" placeholder="学历关键词" value={educationFilter} onChange={(e) => setEducationFilter(e.target.value)} />
          <select className="input" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
            <option value="">风险不限</option>
            <option value="true">存在风险点</option>
            <option value="false">无风险点</option>
          </select>
          <select className="input" value={lowConfidenceFilter} onChange={(e) => setLowConfidenceFilter(e.target.value)}>
            <option value="">置信度不限</option>
            <option value="true">有待确认字段</option>
            <option value="false">无待确认字段</option>
          </select>
        </div>
      </section>

      <section className="panel mb-5 flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <p className="text-sm text-muted-foreground">已选择 {selectedIds.length} 位候选人</p>
        <div className="flex flex-wrap gap-2">
          <button disabled={!selectedIds.length || bulkSaving} onClick={() => void runBulkStatus("pending_contact")} className="btn-secondary">
            标记待沟通
          </button>
          <button disabled={!selectedIds.length || bulkSaving} onClick={() => void runBulkStatus("rejected")} className="btn-secondary">
            批量淘汰
          </button>
          <button disabled={!selectedIds.length || bulkSaving} onClick={() => void runBulkArchive()} className="btn-secondary">
            加入人才库
          </button>
          <button disabled={!selectedIds.length || bulkSaving} onClick={() => void runBulkMatch()} className="btn-primary">
            {bulkSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            重新评分
          </button>
        </div>
      </section>

      <section className="panel overflow-hidden">
        {loading ? (
          <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在加载候选人
          </div>
        ) : sorted.length ? (
          <div className="overflow-x-auto">
            <div className="data-grid-head grid-cols-[44px_1.15fr_0.9fr_0.55fr_0.75fr_0.85fr_0.7fr]">
              <span>
                <input
                  type="checkbox"
                  checked={allVisibleSelected}
                  onChange={(event) =>
                    setSelectedIds(event.target.checked ? sorted.map((item) => item.candidate.id) : [])
                  }
                />
              </span>
              <span>候选人</span>
              <span>岗位/城市</span>
              <span>匹配分</span>
              <span>推荐等级</span>
              <span>状态</span>
              <span>操作</span>
            </div>
            <div className="divide-y divide-border">
              {sorted.map((item) => (
                <div key={item.candidate.id} className="data-grid-row grid-cols-[44px_1.15fr_0.9fr_0.55fr_0.75fr_0.85fr_0.7fr]">
                  <span>
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.candidate.id)}
                      onChange={() => toggleCandidate(item.candidate.id)}
                    />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-medium">{item.candidate.name || "姓名待确认"}</p>
                    <p className="mt-1 truncate text-xs text-muted-foreground">{item.candidate.phone || item.candidate.email || "联系方式待确认"}</p>
                  </div>
                  <div className="min-w-0 text-muted-foreground">
                    <p className="truncate">{item.candidate.current_title || "岗位待确认"}</p>
                    <p className="mt-1 truncate text-xs">{item.candidate.city || "城市待确认"}</p>
                  </div>
                  <span className="font-semibold">{item.match?.score ?? "-"}</span>
                  <span className="text-muted-foreground">{item.match?.level ?? "未评分"}</span>
                  <select
                    className="input h-9 py-1"
                    disabled={statusSavingId === item.candidate.id}
                    value={item.status?.status ?? "pending"}
                    onChange={(event) => void changeStatus(item.candidate.id, event.target.value as CandidateStatusValue)}
                  >
                    {statusOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                  <Link className="text-sm font-semibold text-primary" href={`/jobs/${params.jobId}/candidates/${item.candidate.id}`}>
                    查看详情
                  </Link>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-5">
            <EmptyState
              title="暂无候选人"
              description="上传简历并完成解析后，候选人会按匹配分显示在这里。"
              action={
                <Link href={`/jobs/${params.jobId}/resumes/upload`} className="btn-primary">
                  上传简历
                </Link>
              }
            />
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel px-4 py-3">
      <p className="text-xs font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function formatBulkResult(action: string, requestedCount: number, successCount: number) {
  if (successCount === requestedCount) {
    return `${action}完成：成功处理 ${successCount} 位候选人。`;
  }
  return `${action}部分完成：成功处理 ${successCount} / ${requestedCount} 位候选人，未处理项可能已不存在或不属于当前岗位。`;
}
