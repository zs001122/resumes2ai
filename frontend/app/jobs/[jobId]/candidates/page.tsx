"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Loader2, RefreshCw, Upload } from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  CandidateListItem,
  CandidateStatusValue,
  listCandidates,
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
  const [loading, setLoading] = useState(true);
  const [statusSavingId, setStatusSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadCandidates() {
    setLoading(true);
    setError(null);
    try {
      setItems(
        await listCandidates(params.jobId, {
          status: statusFilter,
          level: levelFilter,
          min_score: minScore,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "候选人列表加载失败");
    } finally {
      setLoading(false);
    }
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

      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <Stat label="候选人" value={stats.total} />
        <Stat label="强匹配" value={stats.high} />
        <Stat label="待筛选" value={stats.pending} />
      </div>

      <section className="panel mb-5 p-4">
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto]">
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
          <button onClick={() => void loadCandidates()} className="btn-primary">
            应用筛选
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
            <div className="data-grid-head grid-cols-[1.15fr_0.9fr_0.55fr_0.75fr_0.85fr_0.7fr]">
              <span>候选人</span>
              <span>岗位/城市</span>
              <span>匹配分</span>
              <span>推荐等级</span>
              <span>状态</span>
              <span>操作</span>
            </div>
            <div className="divide-y divide-border">
              {sorted.map((item) => (
                <div key={item.candidate.id} className="data-grid-row grid-cols-[1.15fr_0.9fr_0.55fr_0.75fr_0.85fr_0.7fr]">
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
