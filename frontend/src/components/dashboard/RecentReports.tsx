import { Badge } from "@/components/ui/badge";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import type { RecentReport } from "@/data/dashboardData";

type RecentReportsProps = {
  reports: RecentReport[];
};

const riskVariant = {
  Low: "success",
  Medium: "warning",
  High: "destructive",
} as const;

export function RecentReports({ reports }: RecentReportsProps) {
  return (
    <DashboardCard
      title="Recent reports"
      description="Placeholder impact reports generated from recent changes."
    >
      <div className="space-y-3">
        {reports.map((report) => (
          <div key={report.id} className="rounded-md border p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="text-sm font-medium">{report.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {report.generatedAt} • {report.affectedItems} affected items
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                <Badge variant={riskVariant[report.risk]}>{report.risk}</Badge>
                <Badge variant="secondary">{report.status}</Badge>
              </div>
            </div>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}
