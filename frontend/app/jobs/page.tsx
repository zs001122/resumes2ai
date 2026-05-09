export default function JobsPage() {
  return (
    <main className="min-h-screen bg-muted px-6 py-8">
      <section className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">岗位列表</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Phase 1 将在这里实现岗位创建、JD 解析和筛选标准确认。
            </p>
          </div>
          <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
            创建岗位
          </button>
        </div>

        <div className="mt-6 rounded-lg border border-border bg-background p-8 text-sm text-muted-foreground">
          暂无岗位。项目骨架阶段仅保留页面入口。
        </div>
      </section>
    </main>
  );
}
