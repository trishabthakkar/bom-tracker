import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, AlertCircle } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { RiskBadge } from "@/components/reports/RiskBadge";
import { Button } from "@/components/ui/button";
import { getReport, type SavedImpactReportDetail } from "@/lib/reportApi";

export function ReportDetailPage() {
  const { reportId } = useParams();
  const [report, setReport] = useState<SavedImpactReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) {
      setError("Report id is missing.");
      setLoading(false);
      return;
    }

    getReport(reportId)
      .then(setReport)
      .catch((reportError) => {
        setError(reportError instanceof Error ? reportError.message : "Unable to load report.");
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading report...</p>;
  }

  if (error || !report) {
    return (
      <div className="space-y-4">
        <Button asChild variant="outline" size="sm">
          <Link to="/reports">
            <ArrowLeft className="h-4 w-4" />
            Back to reports
          </Link>
        </Button>
        <div
          className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error ?? "Report was not found."}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Button asChild variant="outline" size="sm">
            <Link to="/reports">
              <ArrowLeft className="h-4 w-4" />
              Back to reports
            </Link>
          </Button>
          <h1 className="mt-4 text-2xl font-semibold tracking-normal">Report #{report.id}</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{report.summary}</p>
        </div>
        <RiskBadge level={report.risk_level} />
      </div>

      <section className="grid gap-4 lg:grid-cols-3">
        <DashboardCard title="Affected part">
          <p className="text-2xl font-semibold">{report.affected_part ?? "-"}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Effective date: {report.effective_date ?? "-"}
          </p>
        </DashboardCard>
        <DashboardCard title="Risk score">
          <p className="text-2xl font-semibold">{report.risk_score}/100</p>
          <p className="mt-1 text-sm text-muted-foreground">{report.risk_level} downstream risk</p>
        </DashboardCard>
        <DashboardCard title="Source records">
          <p className="text-sm text-muted-foreground">BOM import #{report.bom_import_id}</p>
          <p className="text-sm text-muted-foreground">ECO record #{report.eco_record_id ?? "-"}</p>
        </DashboardCard>
      </section>

      <DashboardCard title="Risk reasons">
        <ul className="space-y-2 text-sm text-muted-foreground">
          {report.report.risk.reasons.map((reason) => (
            <li key={reason} className="rounded-md border p-3">
              {reason}
            </li>
          ))}
        </ul>
      </DashboardCard>

      <DashboardCard title="Affected assemblies">
        {report.report.affected_assemblies.length === 0 ? (
          <p className="text-sm text-muted-foreground">No matching assemblies were found.</p>
        ) : (
          <div className="space-y-3">
            {report.report.affected_assemblies.map((assembly) => (
              <div key={assembly.part_number} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{assembly.part_number}</p>
                <p className="mt-1 text-muted-foreground">
                  Parents: {assembly.affected_parents.join(", ") || "-"}
                </p>
                <p className="text-muted-foreground">
                  Children: {assembly.affected_children.join(", ") || "-"}
                </p>
              </div>
            ))}
          </div>
        )}
      </DashboardCard>

      <section className="grid gap-4 xl:grid-cols-2">
        <DashboardCard title="Downstream records">
          <div className="space-y-3">
            {report.report.downstream_records.map((record) => (
              <div key={record.record_type} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{record.record_type}</p>
                <p className="mt-1 text-muted-foreground">{record.impact}</p>
              </div>
            ))}
          </div>
        </DashboardCard>

        <DashboardCard title="Suggested updates">
          <div className="space-y-3">
            {report.report.suggested_updates.map((update) => (
              <div key={`${update.area}-${update.action}`} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{update.area}</p>
                <p className="mt-1 text-muted-foreground">{update.action}</p>
              </div>
            ))}
          </div>
        </DashboardCard>
      </section>
    </div>
  );
}
