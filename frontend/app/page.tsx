import Link from "next/link";
import { kpis, recentActions, upcomingSchedule, type KpiTone } from "@/lib/mock/dashboard";

const toneRing: Record<KpiTone, string> = {
  primary: "text-primary",
  accent: "text-accent",
  warning: "text-amber-600",
  neutral: "text-foreground",
};

const toneBar: Record<KpiTone, string> = {
  primary: "bg-primary",
  accent: "bg-accent",
  warning: "bg-amber-500",
  neutral: "bg-slate-400",
};

const statusBadge: Record<string, string> = {
  ok: "bg-accent/15 text-accent",
  pending: "bg-amber-500/15 text-amber-700",
  failed: "bg-destructive/15 text-destructive",
};

const maxLoad = Math.max(...upcomingSchedule.map((d) => d.load));

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
          <p className="text-sm text-foreground/60">
            Scheduling overview for the Fall 2026 term.
          </p>
        </div>
        <Link
          href="/import"
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
        >
          Import data
        </Link>
      </div>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((k) => (
          <div
            key={k.id}
            className="rounded-lg border border-border bg-white p-4 shadow-sm dark:bg-slate-900"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-foreground/50">
              {k.label}
            </p>
            <p className={`mt-1 text-3xl font-bold ${toneRing[k.tone]}`}>{k.value}</p>
            <p className="mt-1 text-xs text-foreground/60">{k.hint}</p>
            {typeof k.progress === "number" && (
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-border">
                <div
                  className={`h-full ${toneBar[k.tone]}`}
                  style={{ width: `${k.progress}%` }}
                />
              </div>
            )}
          </div>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-white p-4 shadow-sm lg:col-span-2 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Recent actions</h3>
          <ul className="divide-y divide-border">
            {recentActions.map((a) => (
              <li key={a.id} className="flex items-center justify-between py-2 text-sm">
                <div className="min-w-0">
                  <p className="truncate text-foreground">
                    <span className="font-semibold">{a.actor}</span>{" "}
                    <span className="text-foreground/60">{a.verb}</span>{" "}
                    <span className="font-medium">{a.target}</span>
                  </p>
                  <p className="text-xs text-foreground/50">{a.at}</p>
                </div>
                <span
                  className={`ml-3 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${statusBadge[a.status]}`}
                >
                  {a.status}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-border bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Weekly load</h3>
          <div className="flex h-40 items-end justify-between gap-2">
            {upcomingSchedule.map((d) => (
              <div key={d.day} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-primary/80"
                  style={{ height: `${(d.load / maxLoad) * 100}%` }}
                  title={`${d.load} sessions`}
                />
                <span className="text-xs text-foreground/60">{d.day}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-foreground/50">
            Peak load: <span className="font-semibold text-foreground">Wed</span> (61 sessions)
          </p>
        </div>
      </section>
    </div>
  );
}
