import type { ActivityItem } from "@/data/dashboardData";
import { DashboardCard } from "@/components/dashboard/DashboardCard";

type RecentActivityProps = {
  activity: ActivityItem[];
};

export function RecentActivity({ activity }: RecentActivityProps) {
  return (
    <DashboardCard
      title="Recent activity"
      description="A realistic preview of the future audit trail."
      className="xl:col-span-2"
    >
      <div className="space-y-4">
        {activity.map((item, index) => (
          <div key={item.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-primary" />
              {index < activity.length - 1 ? (
                <span className="mt-2 h-full min-h-10 w-px bg-border" />
              ) : null}
            </div>
            <div className="min-w-0 pb-1">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <p className="text-sm font-medium">{item.title}</p>
                <span className="text-xs text-muted-foreground">{item.time}</span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
            </div>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}
