import Link from "next/link";

const modules = [
  { name: "岗位管理", description: "创建岗位、解析 JD、确认筛选标准", href: "/jobs" },
  { name: "简历上传", description: "上传简历、查看解析状态、进入人工修正", href: "/jobs" },
  { name: "候选人筛选", description: "按匹配分排序，复核详情并流转状态", href: "/jobs" },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-muted">
      <section className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-col gap-3">
          <p className="text-sm font-medium text-muted-foreground">Resumes2AI MVP</p>
          <h1 className="text-3xl font-semibold">AI 简历筛选工作台</h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground">
            当前项目骨架已建立。下一步将按 MVP 任务拆解实现岗位管理、简历上传、解析修正和候选人筛选闭环。
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-3">
          {modules.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="rounded-lg border border-border bg-background p-5 transition hover:border-primary"
            >
              <h2 className="text-lg font-semibold">{item.name}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
