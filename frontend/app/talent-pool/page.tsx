"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Archive, Loader2, RefreshCw, Search, X } from "lucide-react";

import { EmptyState, Notice, WorkspaceShell } from "@/components/WorkspaceShell";
import {
  TalentPoolCandidate,
  listTalentPoolCandidates,
  removeCandidateFromTalentPool,
} from "@/lib/api";

const statusLabel: Record<string, string> = {
  pending: "待筛选",
  favorite: "已收藏",
  pending_contact: "待沟通",
  rejected: "已淘汰",
  archived: "已入库",
};

export default function TalentPoolPage() {
  const [items, setItems] = useState<TalentPoolCandidate[]>([]);
  const [query, setQuery] = useState("");
  const [skill, setSkill] = useState("");
  const [city, setCity] = useState("");
  const [education, setEducation] = useState("");
  const [minYears, setMinYears] = useState("");
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadTalentPool() {
    setLoading(true);
    setError(null);
    try {
      setItems(
        await listTalentPoolCandidates({
          query,
          skill,
          city,
          education,
          min_years: minYears,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "人才库加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function removeFromPool(candidateId: string) {
    setRemovingId(candidateId);
    setError(null);
    try {
      await removeCandidateFromTalentPool(candidateId);
      await loadTalentPool();
    } catch (err) {
      setError(err instanceof Error ? err.message : "移出人才库失败");
    } finally {
      setRemovingId(null);
    }
  }

  useEffect(() => {
    void loadTalentPool();
  }, []);

  const stats = useMemo(
    () => ({
      total: items.length,
      withTags: items.filter((item) => item.tags.length > 0).length,
      high: items.filter((item) => (item.latest_match?.score ?? 0) >= 80).length,
    }),
    [items],
  );

  return (
    <WorkspaceShell
      title="轻量人才库"
      description="沉淀已入库候选人，支持跨岗位搜索、标签查看和历史岗位回溯。"
      actions={
        <button onClick={() => void loadTalentPool()} className="btn-secondary">
          <RefreshCw className="h-4 w-4" />
          刷新
        </button>
      }
    >
      {error ? (
        <Notice
          tone="error"
          action={
            <button onClick={() => void loadTalentPool()} className="btn-secondary h-8 text-xs">
              重试
            </button>
          }
        >
          {error}
        </Notice>
      ) : null}

      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <Stat label="入库候选人" value={stats.total} />
        <Stat label="已有标签" value={stats.withTags} />
        <Stat label="高匹配" value={stats.high} />
      </div>

      <section className="panel mb-5 p-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-[1.2fr_1fr_1fr_1fr_1fr_auto]">
          <input className="input" placeholder="搜索姓名、联系方式、岗位、公司" value={query} onChange={(event) => setQuery(event.target.value)} />
          <input className="input" placeholder="技能" value={skill} onChange={(event) => setSkill(event.target.value)} />
          <input className="input" placeholder="城市" value={city} onChange={(event) => setCity(event.target.value)} />
          <input className="input" placeholder="学历" value={education} onChange={(event) => setEducation(event.target.value)} />
          <input
            className="input"
            inputMode="numeric"
            placeholder="最低年限"
            value={minYears}
            onChange={(event) => setMinYears(event.target.value.replace(/[^\d.]/g, ""))}
          />
          <button onClick={() => void loadTalentPool()} className="btn-primary">
            <Search className="h-4 w-4" />
            搜索
          </button>
        </div>
      </section>

      <section className="panel overflow-hidden">
        <div className="border-b border-border px-5 py-4">
          <h2 className="text-base font-semibold">入库候选人</h2>
        </div>
        {loading ? (
          <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在加载人才库
          </div>
        ) : items.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="暂无入库候选人"
              description="在候选人列表或详情页将候选人加入人才库后，会在这里沉淀为可复用人选。"
              action={
                <Link href="/jobs" className="btn-primary">
                  查看岗位
                </Link>
              }
            />
          </div>
        ) : (
          <div className="divide-y divide-border">
            {items.map((item) => {
              const latestHistory = item.job_history[0];
              return (
                <div key={item.candidate.id} className="grid gap-4 px-5 py-4 lg:grid-cols-[1.2fr_1fr_1fr_0.8fr_auto] lg:items-center">
                  <div className="min-w-0">
                    <p className="truncate font-semibold">{item.candidate.name || "姓名待确认"}</p>
                    <p className="mt-1 truncate text-sm text-muted-foreground">
                      {item.candidate.current_title || "岗位待确认"} / {item.candidate.city || "城市待确认"}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {item.tags.length ? (
                        item.tags.map((tag) => <span key={tag.id} className="status-pill">{tag.name}</span>)
                      ) : (
                        <span className="text-xs text-muted-foreground">暂无标签</span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <p>{item.candidate.highest_education || "学历待确认"}</p>
                    <p className="mt-1">{item.candidate.years_of_experience ?? "-"} 年经验</p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <p className="truncate">{latestHistory?.job_title || "暂无岗位历史"}</p>
                    <p className="mt-1">{statusLabel[latestHistory?.candidate_status || ""] || latestHistory?.candidate_status || "-"}</p>
                  </div>
                  <div>
                    <p className="text-2xl font-semibold">{item.latest_match?.score ?? "-"}</p>
                    <p className="text-sm text-muted-foreground">{item.latest_match?.level || "未评分"}</p>
                  </div>
                  <div className="flex flex-wrap gap-2 lg:justify-end">
                    {latestHistory ? (
                      <Link href={`/jobs/${latestHistory.job_id}/candidates/${item.candidate.id}`} className="btn-secondary h-9 text-xs">
                        查看详情
                      </Link>
                    ) : null}
                    <button
                      onClick={() => void removeFromPool(item.candidate.id)}
                      disabled={removingId === item.candidate.id}
                      className="btn-secondary h-9 text-xs"
                    >
                      {removingId === item.candidate.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <X className="h-3.5 w-3.5" />}
                      移出
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="panel px-4 py-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-muted-foreground">{label}</p>
        <Archive className="h-4 w-4 text-muted-foreground" />
      </div>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
