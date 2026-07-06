import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, LayoutDashboard, Upload, Users } from "lucide-react";

import { WorkspaceShell } from "@/components/WorkspaceShell";

const actions = [
  { title: "查看总览", href: "/dashboard", description: "处理今日待办、异常和最近活动", icon: LayoutDashboard, primary: true },
  { title: "管理岗位", href: "/jobs", description: "查看开放岗位和候选人进展", icon: BriefcaseBusiness },
  { title: "上传简历", href: "/resumes/upload", description: "进入统一上传入口并触发解析", icon: Upload },
  { title: "人才库", href: "/talent-pool", description: "检索已沉淀候选人和历史记录", icon: Users },
];

export default function HomePage() {
  return (
    <WorkspaceShell
      title="招聘初筛工作台"
      description="从岗位、简历解析、人工修正到候选人流转，围绕当前招聘初筛闭环工作。"
      actions={
        <Link href="/dashboard" className="btn-primary">
          进入总览
          <ArrowRight className="h-4 w-4" />
        </Link>
      }
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {actions.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.title}
              href={item.href}
              className={item.primary ? "panel group p-5 ring-1 ring-primary/20" : "panel group p-5"}
            >
              <div className="flex items-start justify-between gap-4">
                <div className={item.primary ? "flex h-10 w-10 items-center justify-center rounded-md bg-primary text-white" : "flex h-10 w-10 items-center justify-center rounded-md bg-slate-100 text-slate-700"}>
                  <Icon className="h-5 w-5" />
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-foreground" />
              </div>
              <h2 className="mt-4 text-base font-semibold">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
            </Link>
          );
        })}
      </section>

      <section className="mt-5 grid gap-5 lg:grid-cols-[1fr_360px]">
        <div className="panel overflow-hidden">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold">当前主线</h2>
          </div>
          <div className="grid gap-0 divide-y divide-border md:grid-cols-3 md:divide-x md:divide-y-0">
            <Stage title="V2 稳定化" value="主流程可验收" />
            <Stage title="vNext Parser" value="证据闭环实验" />
            <Stage title="人工修正" value="来源回写已接入" />
          </div>
        </div>
        <aside className="panel p-5">
          <h2 className="text-base font-semibold">建议入口</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">日常验收优先从总览进入；处理具体岗位时从岗位列表进入；批量新增简历时使用统一上传。</p>
          <Link href="/dashboard" className="btn-secondary mt-5 w-full">
            打开总览
          </Link>
        </aside>
      </section>
    </WorkspaceShell>
  );
}

function Stage({ title, value }: { title: string; value: string }) {
  return (
    <div className="px-5 py-4">
      <p className="text-xs font-semibold uppercase text-muted-foreground">{title}</p>
      <p className="mt-2 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}
