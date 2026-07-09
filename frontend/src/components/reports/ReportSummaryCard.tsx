import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/reports/RiskBadge";
import type { SavedImpactReport } from "@/lib/reportApi";

type ReportSummaryCardProps = {
  report: SavedImpactReport;
};

export function ReportSummaryCard({ report }: ReportSummaryCardProps) {
  return (
    <DashboardCard
      title={`Report #${report.id}`}
      description={new Date(report.created_at).toLocaleString()}
      action={<RiskBadge level={report.risk_level} />}
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{report.review_status.replace(/_/g, " ")}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{report.summary}</p>
        <div className="grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <p className="text-muted-foreground">Affected part</p>
            <p className="font-medium">{report.affected_part ?? "-"}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Risk score</p>
            <p className="font-medium">{report.risk_score}/100</p>
          </div>
          <div>
            <p className="text-muted-foreground">BOM upload</p>
            <p className="font-medium">#{report.bom_upload_id}</p>
          </div>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to={`/reports/${report.id}`}>
            Open report
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </DashboardCard>
  );
}
