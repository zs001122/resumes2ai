import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, FileUp, ListChecks, Users } from "lucide-react";

import { WorkspaceShell } from "@/components/WorkspaceShell";

const steps = [
  {
    title: "创建岗位",
    description: "录入 JD，确认必备条件、加分项和排除项。",
    icon: BriefcaseBusiness,
  },
  {
    title: "上传简历",
    description: "批量上传 PDF、DOCX、TXT，自动抽取结构化字段。",
    icon: FileUp,
  },
  {
    title: "复核修正",
    description: "对照原文检查关键字段，必要时人工修正。",
    icon: ListChecks,
  },
  {
    title: "筛选流转",
    description: "按匹配分排序，进入待沟通、淘汰或入库状态。",
    icon: Users,
  },
];

export default function HomePage() {
  return (
    <WorkspaceShell
      title="AI 简历筛选工作台"
      description="围绕岗位创建、简历解析、匹配评分和候选人状态流转完成 MVP 初筛闭环。"
      actions={
        <Link href="/jobs/new" className="btn-primary">
          创建岗位
          <ArrowRight className="h-4 w-4" />
        </Link>
      }
    >
      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <section className="panel p-6">
          <div className="grid gap-4 md:grid-cols-2">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={step.title} className="rounded-md border border-border bg-background p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground">步骤 {index + 1}</p>
                      <h2 className="text-base font-semibold">{step.title}</h2>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{step.description}</p>
                </div>
              );
            })}
          </div>
        </section>

        <aside className="panel p-5">
          <h2 className="text-base font-semibold">验收路径</h2>
          <ol className="mt-4 space-y-3 text-sm text-muted-foreground">
            <li>1. 创建岗位并保存筛选标准</li>
            <li>2. 上传样例简历并完成解析</li>
            <li>3. 进入候选人详情查看评分</li>
            <li>4. 修正字段后重新评分</li>
            <li>5. 在候选人列表修改状态</li>
          </ol>
          <Link href="/jobs" className="btn-secondary mt-5 w-full">
            进入岗位列表
          </Link>
        </aside>
      </div>
    </WorkspaceShell>
  );
}
