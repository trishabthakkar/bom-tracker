import { useEffect, useState } from "react";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { RecentReports } from "@/components/dashboard/RecentReports";
import { RecentUploads } from "@/components/dashboard/RecentUploads";
import {
  metrics,
  quickActions,
  recentActivity,
  recentReports,
  recentUploads,
} from "@/data/dashboardData";

export function HomePage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => setLoading(false), 450);
    return () => window.clearTimeout(timeout);
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Dashboard</p>
          <h1 className="text-2xl font-semibold tracking-normal">
            Engineering change workspace
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Monitor recent inputs, impact reports, and dependency analysis activity.
          </p>
        </div>
        <p className="text-xs text-muted-foreground">Last refreshed 4 minutes ago</p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <QuickActions actions={quickActions} />
        <RecentUploads uploads={recentUploads} />
        <RecentReports reports={recentReports} />
        <RecentActivity activity={recentActivity} />
      </section>
    </div>
  );
}
