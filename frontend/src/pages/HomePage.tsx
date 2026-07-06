import { useEffect, useState } from "react";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { RecentReports } from "@/components/dashboard/RecentReports";
import { RecentUploads } from "@/components/dashboard/RecentUploads";
import { quickActions, type ActivityItem, type Metric, type RecentReport, type RecentUpload } from "@/data/dashboardData";
import { getBomImports, type BomImport } from "@/lib/bomImportApi";
import { getEcoRecords, type EcoRecord } from "@/lib/ecoRecordApi";
import { getReports, type SavedImpactReport } from "@/lib/reportApi";
import { getUploadHistory, type UploadedFile } from "@/lib/uploadApi";

export function HomePage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [recentReports, setRecentReports] = useState<RecentReport[]>([]);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getUploadHistory(), getReports(), getBomImports(), getEcoRecords()])
      .then(([uploads, reports, imports, ecoRecords]) => {
        setMetrics(buildMetrics(uploads, reports, imports, ecoRecords));
        setRecentUploads(uploads.slice(0, 4).map(toRecentUpload));
        setRecentReports(reports.slice(0, 3).map(toRecentReport));
        setRecentActivity(buildActivity(uploads, reports, imports, ecoRecords));
      })
      .catch((dashboardError) => {
        setError(
          dashboardError instanceof Error
            ? dashboardError.message
            : "Unable to load dashboard data.",
        );
      })
      .finally(() => setLoading(false));
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
        <p className="text-xs text-muted-foreground">Live workspace data</p>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

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

function buildMetrics(
  uploads: UploadedFile[],
  reports: SavedImpactReport[],
  imports: BomImport[],
  ecoRecords: EcoRecord[],
): Metric[] {
  const highRisk = reports.filter((report) => report.risk_level === "High").length;
  const affectedItems = reports.reduce((total, report) => total + (report.affected_part ? 1 : 0), 0);

  return [
    {
      label: "Uploads",
      value: String(uploads.length),
      detail: "BOMs, ECOs, and documents",
      trend: `${imports.length} normalized BOM imports`,
    },
    {
      label: "Reports generated",
      value: String(reports.length),
      detail: "Persisted impact reports",
      trend: `${highRisk} high risk`,
    },
    {
      label: "Parsed ECOs",
      value: String(ecoRecords.length),
      detail: "Saved engineering changes",
      trend: "Rule-based parser active",
    },
    {
      label: "Affected parts",
      value: String(affectedItems),
      detail: "From saved reports",
      trend: "Based on persisted report history",
    },
  ];
}

function toRecentUpload(upload: UploadedFile): RecentUpload {
  return {
    id: String(upload.id),
    filename: upload.original_filename,
    type: upload.upload_category === "bom" ? "BOM" : upload.upload_category === "eco" ? "ECO" : "Manual",
    uploadedBy: "You",
    uploadedAt: new Date(upload.created_at).toLocaleString(),
    status: upload.status === "stored" ? "Validated" : "Processing",
  };
}

function toRecentReport(report: SavedImpactReport): RecentReport {
  return {
    id: String(report.id),
    title: report.summary,
    generatedAt: new Date(report.created_at).toLocaleString(),
    risk: report.risk_level as RecentReport["risk"],
    affectedItems: report.affected_part ? 1 : 0,
    status: report.status === "generated" ? "Ready" : "Draft",
  };
}

function buildActivity(
  uploads: UploadedFile[],
  reports: SavedImpactReport[],
  imports: BomImport[],
  ecoRecords: EcoRecord[],
): ActivityItem[] {
  return [
    ...reports.slice(0, 2).map((report) => ({
      id: `report-${report.id}`,
      title: "Impact report generated",
      description: report.summary,
      time: new Date(report.created_at).toLocaleString(),
    })),
    ...imports.slice(0, 2).map((bomImport) => ({
      id: `import-${bomImport.id}`,
      title: "BOM normalized",
      description: `${bomImport.filename} imported with ${bomImport.row_count} rows.`,
      time: new Date(bomImport.created_at).toLocaleString(),
    })),
    ...ecoRecords.slice(0, 1).map((record) => ({
      id: `eco-${record.id}`,
      title: "ECO parsed",
      description: `${record.change_type ?? "Change"} for ${record.old_part ?? record.new_part ?? "unknown part"}.`,
      time: new Date(record.created_at).toLocaleString(),
    })),
    ...uploads.slice(0, 1).map((upload) => ({
      id: `upload-${upload.id}`,
      title: "File uploaded",
      description: upload.original_filename,
      time: new Date(upload.created_at).toLocaleString(),
    })),
  ].slice(0, 4);
}
