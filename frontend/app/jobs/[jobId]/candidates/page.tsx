"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Loader2, RefreshCw, Upload } from "lucide-react";

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

  return (
    <main className="min-h-screen bg-muted px-6 py-8">
      <section className="mx-auto max-w-7xl">
        <Link href={`/jobs/${params.jobId}`} className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <ArrowLeft className="h-4 w-4" />
          返回岗位详情
        </Link>

        <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">候选人列表</h1>
            <p className="mt-2 text-sm text-muted-foreground">按匹配分排序，筛选并推进初筛状态。</p>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/jobs/${params.jobId}/resumes/upload`}
              className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
            >
              <Upload className="h-4 w-4" />
              上传简历
            </Link>
            <button
              onClick={() => void loadCandidates()}
              className="inline-flex h-10 items-center gap-2 rounded-md border border-border bg-background px-4 text-sm font-medium"
            >
              <RefreshCw className="h-4 w-4" />
              刷新
            </button>
          </div>
        </div>

        <div className="mt-6 grid gap-3 rounded-lg border border-border bg-background p-4 md:grid-cols-4">
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
          <button onClick={() => void loadCandidates()} className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground">
            应用筛选
          </button>
        </div>

        {error ? (
          <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <div>{error}</div>
            <button onClick={() => void loadCandidates()} className="mt-3 inline-flex h-8 items-center gap-2 rounded-md border border-red-200 bg-white px-3 text-xs font-medium">
              <RefreshCw className="h-3.5 w-3.5" />
              重试
            </button>
          </div>
        ) : null}

        <div className="mt-6 overflow-hidden rounded-lg border border-border bg-background">
          <div className="grid grid-cols-[1.1fr_0.8fr_0.7fr_0.7fr_0.9fr_0.9fr] border-b border-border px-4 py-3 text-xs font-medium text-muted-foreground">
            <span>候选人</span>
            <span>岗位/城市</span>
            <span>匹配分</span>
            <span>推荐等级</span>
            <span>状态</span>
            <span>操作</span>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              正在加载候选人
            </div>
          ) : sorted.length ? (
            <div className="divide-y divide-border">
              {sorted.map((item) => (
                <div key={item.candidate.id} className="grid grid-cols-[1.1fr_0.8fr_0.7fr_0.7fr_0.9fr_0.9fr] items-center px-4 py-4 text-sm">
                  <div>
                    <p className="font-medium">{item.candidate.name || "姓名待确认"}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{item.candidate.phone || "手机号待确认"}</p>
                  </div>
                  <div className="text-muted-foreground">
                    <p>{item.candidate.current_title || "岗位待确认"}</p>
                    <p className="mt-1 text-xs">{item.candidate.city || "城市待确认"}</p>
                  </div>
                  <span className="font-semibold">{item.match?.score ?? "-"}</span>
                  <span className="text-muted-foreground">{item.match?.level ?? "未评分"}</span>
                  <select
                    className="input"
                    disabled={statusSavingId === item.candidate.id}
                    value={item.status?.status ?? "pending"}
                    onChange={(event) => void changeStatus(item.candidate.id, event.target.value as CandidateStatusValue)}
                  >
                    {statusOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                  <Link className="text-sm font-medium text-primary" href={`/jobs/${params.jobId}/candidates/${item.candidate.id}`}>
                    查看详情
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-sm text-muted-foreground">
              暂无候选人。请先上传简历，系统完成解析和评分后会显示在这里。
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
