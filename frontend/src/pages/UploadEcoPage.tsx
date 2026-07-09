import { useCallback, useEffect, useState } from "react";
import { AlertCircle, RefreshCw, Save } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { JobStatusPanel } from "@/components/jobs/JobStatusPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UploadPageShell } from "@/components/upload/UploadPageShell";
import { getEcoRecords, saveEcoText, type EcoRecord } from "@/lib/ecoRecordApi";
import { pollJobUntilFinished, startEcoUploadParseJob, type Job } from "@/lib/jobApi";
import type { UploadedFile } from "@/lib/uploadApi";

export function UploadEcoPage() {
  const [ecoText, setEcoText] = useState(
    "Replace old part PN-1212 with new part PN-2212. Reason: supplier obsolescence. Effective date: 2026-08-15.",
  );
  const [records, setRecords] = useState<EcoRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refreshRecords = useCallback(async () => {
    setLoading(true);
    try {
      setRecords(await getEcoRecords());
    } catch (recordError) {
      setError(recordError instanceof Error ? recordError.message : "Unable to load ECO records.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshRecords();
  }, [refreshRecords]);

  async function handleSaveEco() {
    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      const saved = await saveEcoText(ecoText);
      setMessage(`Saved ECO record #${saved.id}.`);
      await refreshRecords();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save ECO.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUploadComplete(upload: UploadedFile) {
    setSaving(true);
    setError(null);
    setMessage(null);
    setJob(null);

    try {
      const queuedJob = await startEcoUploadParseJob(upload.id);
      const finishedJob = await pollJobUntilFinished(queuedJob, setJob);

      if (finishedJob.status === "failed") {
        throw new Error(finishedJob.error_message ?? "Unable to parse ECO upload.");
      }

      setMessage(`Uploaded and saved ECO record #${finishedJob.result_json?.eco_record_id}.`);
      await refreshRecords();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to parse ECO upload.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <UploadPageShell
        title="Upload ECO"
        description="Upload ECO PDFs for future document-backed change interpretation workflows."
        category="eco"
        acceptedExtensions={[".pdf"]}
        acceptedLabels={["PDF"]}
        onUploadComplete={handleUploadComplete}
      />

      {saving || job ? <JobStatusPanel job={job} title="ECO parsing job" /> : null}

      <DashboardCard
        title="Parse ECO text"
        description="Save structured ECO fields for future report generation."
      >
        <div className="space-y-4">
          <textarea
            className="min-h-36 w-full rounded-md border bg-background p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={ecoText}
            onChange={(event) => setEcoText(event.target.value)}
            aria-label="ECO text"
          />
          {message ? (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
              {message}
            </div>
          ) : null}
          {error ? (
            <div
              className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : null}
          <Button type="button" disabled={saving || ecoText.trim().length === 0} onClick={handleSaveEco}>
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : "Save parsed ECO"}
          </Button>
        </div>
      </DashboardCard>

      <DashboardCard
        title="Saved ECO records"
        description="Parsed engineering changes available for downstream report workflows."
        action={
          <Button type="button" size="sm" variant="outline" onClick={refreshRecords}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      >
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading ECO records...</p>
        ) : records.length === 0 ? (
          <p className="text-sm text-muted-foreground">No saved ECO records yet.</p>
        ) : (
          <div className="space-y-3">
            {records.map((record) => (
              <div key={record.id} className="rounded-md border p-3">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">
                      {record.change_type ?? "Unknown change"} •{" "}
                      {record.old_part ?? record.new_part ?? "No part detected"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Record #{record.id} • {new Date(record.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant="secondary">{Math.round(record.confidence * 100)}% confidence</Badge>
                </div>
                {record.reason ? (
                  <p className="mt-2 text-sm text-muted-foreground">{record.reason}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </DashboardCard>
    </div>
  );
}
