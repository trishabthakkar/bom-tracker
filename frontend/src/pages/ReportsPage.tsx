import { useCallback, useEffect, useState } from "react";
import { AlertCircle, FileSearch, RefreshCw, Wand2 } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { JobStatusPanel } from "@/components/jobs/JobStatusPanel";
import { ReportSummaryCard } from "@/components/reports/ReportSummaryCard";
import { Button } from "@/components/ui/button";
import { getBomImports, type BomImport } from "@/lib/bomImportApi";
import { pollJobUntilFinished, startImpactReportJob, type Job } from "@/lib/jobApi";
import {
  getReports,
  type SavedImpactReport,
} from "@/lib/reportApi";

export function ReportsPage() {
  const [reports, setReports] = useState<SavedImpactReport[]>([]);
  const [bomImports, setBomImports] = useState<BomImport[]>([]);
  const [selectedUploadId, setSelectedUploadId] = useState("");
  const [ecoText, setEcoText] = useState(
    "Replace old part PN-1212 with new part PN-2212. Reason: supplier obsolescence. Effective date: 2026-08-15.",
  );
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refreshReports = useCallback(async () => {
    setLoading(true);
    try {
      const [savedReports, savedImports] = await Promise.all([getReports(), getBomImports()]);
      setReports(savedReports);
      setBomImports(savedImports);
      setSelectedUploadId((current) => current || String(savedImports[0]?.upload_id ?? ""));
    } catch (reportError) {
      setError(reportError instanceof Error ? reportError.message : "Unable to load reports.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshReports();
  }, [refreshReports]);

  async function handleGenerateReport() {
    setGenerating(true);
    setError(null);
    setMessage(null);
    setJob(null);

    try {
      const queuedJob = await startImpactReportJob({
        bomUploadId: Number(selectedUploadId),
        ecoText,
      });
      const finishedJob = await pollJobUntilFinished(queuedJob, setJob);

      if (finishedJob.status === "failed") {
        throw new Error(finishedJob.error_message ?? "Unable to generate report.");
      }

      setMessage(`Generated saved report #${finishedJob.result_json?.report_id}.`);
      await refreshReports();
    } catch (reportError) {
      setError(reportError instanceof Error ? reportError.message : "Unable to generate report.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Reports</p>
          <h1 className="text-2xl font-semibold tracking-normal">Impact reports</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Generate and revisit persisted downstream impact reports.
          </p>
        </div>
        <Button type="button" variant="outline" onClick={refreshReports}>
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      <DashboardCard
        title="Generate saved impact report"
        description="Use an uploaded BOM id and ECO text to generate a persisted report."
      >
        <div className="grid gap-4 lg:grid-cols-[280px_1fr_auto] lg:items-end">
          <label className="space-y-2 text-sm">
            <span className="font-medium">Normalized BOM</span>
            <select
              className="h-10 w-full rounded-md border bg-background px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={selectedUploadId}
              onChange={(event) => setSelectedUploadId(event.target.value)}
            >
              <option value="">Select a BOM import</option>
              {bomImports.map((bomImport) => (
                <option key={bomImport.id} value={bomImport.upload_id}>
                  #{bomImport.id} {bomImport.filename} ({bomImport.row_count} rows)
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium">ECO text</span>
            <textarea
              className="min-h-24 w-full rounded-md border bg-background p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={ecoText}
              onChange={(event) => setEcoText(event.target.value)}
            />
          </label>
          <Button
            type="button"
            disabled={generating || !Number(selectedUploadId) || ecoText.trim().length === 0}
            onClick={handleGenerateReport}
          >
            <Wand2 className="h-4 w-4" />
            {generating ? "Generating..." : "Generate"}
          </Button>
        </div>
        {message ? (
          <p className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
            {message}
          </p>
        ) : null}
        {generating || job ? (
          <div className="mt-3">
            <JobStatusPanel job={job} title="Impact report job" />
          </div>
        ) : null}
        {error ? (
          <div
            className="mt-3 flex gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
            role="alert"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}
      </DashboardCard>

      {loading ? (
        <DashboardCard title="Saved reports">
          <p className="text-sm text-muted-foreground">Loading reports...</p>
        </DashboardCard>
      ) : reports.length === 0 ? (
        <DashboardCard title="Saved reports">
          <div className="flex items-start gap-3 text-sm text-muted-foreground">
            <FileSearch className="mt-0.5 h-4 w-4" />
            <p>No saved reports yet. Generate one from an uploaded BOM.</p>
          </div>
        </DashboardCard>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {reports.map((report) => (
            <ReportSummaryCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  );
}
