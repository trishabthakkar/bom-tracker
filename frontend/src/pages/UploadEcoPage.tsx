import { useCallback, useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Edit3, RefreshCw, Save, XCircle } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { JobStatusPanel } from "@/components/jobs/JobStatusPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UploadPageShell } from "@/components/upload/UploadPageShell";
import {
  getEcoRecord,
  getEcoRecords,
  saveEcoText,
  transitionEcoRecord,
  updateEcoRecord,
  type EcoRecord,
  type EcoRecordDetail,
} from "@/lib/ecoRecordApi";
import { pollJobUntilFinished, startEcoUploadParseJob, type Job } from "@/lib/jobApi";
import type { UploadedFile } from "@/lib/uploadApi";

export function UploadEcoPage() {
  const [ecoText, setEcoText] = useState(
    "Replace old part PN-1212 with new part PN-2212. Reason: supplier obsolescence. Effective date: 2026-08-15.",
  );
  const [records, setRecords] = useState<EcoRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<EcoRecordDetail | null>(null);
  const [ecoForm, setEcoForm] = useState({
    change_type: "",
    old_part: "",
    new_part: "",
    reason: "",
    effective_date: "",
    correction_notes: "",
  });
  const [workflowNotes, setWorkflowNotes] = useState("");
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
      await openRecord(saved.id);
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

  async function openRecord(recordId: number) {
    setUpdating(true);
    setError(null);
    try {
      const record = await getEcoRecord(recordId);
      setSelectedRecord(record);
      setEcoForm({
        change_type: record.change_type ?? "",
        old_part: record.old_part ?? "",
        new_part: record.new_part ?? "",
        reason: record.reason ?? "",
        effective_date: record.effective_date ?? "",
        correction_notes: record.correction_notes ?? "",
      });
      setWorkflowNotes(record.approval_notes ?? "");
    } catch (recordError) {
      setError(recordError instanceof Error ? recordError.message : "Unable to open ECO record.");
    } finally {
      setUpdating(false);
    }
  }

  async function handleUpdateRecord() {
    if (!selectedRecord) {
      return;
    }

    setUpdating(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateEcoRecord(selectedRecord.id, {
        change_type: ecoForm.change_type || null,
        old_part: ecoForm.old_part || null,
        new_part: ecoForm.new_part || null,
        reason: ecoForm.reason || null,
        effective_date: ecoForm.effective_date || null,
        correction_notes: ecoForm.correction_notes || null,
      });
      setSelectedRecord(updated);
      setMessage(`Updated ECO record #${updated.id}.`);
      await refreshRecords();
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Unable to update ECO record.");
    } finally {
      setUpdating(false);
    }
  }

  async function handleWorkflowAction(action: "review" | "approve" | "reject") {
    if (!selectedRecord) {
      return;
    }

    setUpdating(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await transitionEcoRecord(selectedRecord.id, action, workflowNotes || null);
      setSelectedRecord(updated);
      setMessage(`ECO record #${updated.id} is now ${updated.workflow_status}.`);
      await refreshRecords();
    } catch (workflowError) {
      setError(workflowError instanceof Error ? workflowError.message : `Unable to ${action} ECO record.`);
    } finally {
      setUpdating(false);
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

      {selectedRecord ? (
        <DashboardCard
          title={`Review ECO record #${selectedRecord.id}`}
          description="Correct parser output and record the review decision before using the ECO downstream."
        >
          <div className="grid gap-4 lg:grid-cols-2">
            <TextInput
              label="Change type"
              value={ecoForm.change_type}
              onChange={(value) => setEcoForm((current) => ({ ...current, change_type: value }))}
            />
            <TextInput
              label="Effective date"
              type="date"
              value={ecoForm.effective_date}
              onChange={(value) => setEcoForm((current) => ({ ...current, effective_date: value }))}
            />
            <TextInput
              label="Old part"
              value={ecoForm.old_part}
              onChange={(value) => setEcoForm((current) => ({ ...current, old_part: value }))}
            />
            <TextInput
              label="New part"
              value={ecoForm.new_part}
              onChange={(value) => setEcoForm((current) => ({ ...current, new_part: value }))}
            />
            <label className="space-y-2 text-sm lg:col-span-2">
              <span className="font-medium">Reason</span>
              <textarea
                className="min-h-24 w-full rounded-md border bg-background p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={ecoForm.reason}
                onChange={(event) => setEcoForm((current) => ({ ...current, reason: event.target.value }))}
              />
            </label>
            <label className="space-y-2 text-sm lg:col-span-2">
              <span className="font-medium">Correction notes</span>
              <textarea
                className="min-h-20 w-full rounded-md border bg-background p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={ecoForm.correction_notes}
                onChange={(event) =>
                  setEcoForm((current) => ({ ...current, correction_notes: event.target.value }))
                }
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button type="button" disabled={updating} onClick={handleUpdateRecord}>
              <Save className="h-4 w-4" />
              Save corrections
            </Button>
            <Button type="button" variant="outline" disabled={updating} onClick={() => handleWorkflowAction("review")}>
              <Edit3 className="h-4 w-4" />
              Mark reviewed
            </Button>
          </div>

          <div className="mt-6 space-y-3 rounded-md border p-3">
            <label className="space-y-2 text-sm">
              <span className="font-medium">Approval notes</span>
              <textarea
                className="min-h-20 w-full rounded-md border bg-background p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={workflowNotes}
                onChange={(event) => setWorkflowNotes(event.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <Button type="button" disabled={updating} onClick={() => handleWorkflowAction("approve")}>
                <CheckCircle2 className="h-4 w-4" />
                Approve
              </Button>
              <Button type="button" variant="outline" disabled={updating} onClick={() => handleWorkflowAction("reject")}>
                <XCircle className="h-4 w-4" />
                Reject
              </Button>
            </div>
          </div>
        </DashboardCard>
      ) : null}

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
                  <div className="flex flex-wrap items-center gap-2">
                    <WorkflowBadge status={record.workflow_status} />
                    <Badge variant="secondary">{Math.round(record.confidence * 100)}% confidence</Badge>
                  </div>
                </div>
                {record.reason ? (
                  <p className="mt-2 text-sm text-muted-foreground">{record.reason}</p>
                ) : null}
                <div className="mt-3">
                  <Button type="button" size="sm" variant="outline" onClick={() => openRecord(record.id)}>
                    <Edit3 className="h-4 w-4" />
                    Review
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </DashboardCard>
    </div>
  );
}

type TextInputProps = {
  label: string;
  value: string;
  type?: string;
  onChange: (value: string) => void;
};

function TextInput({ label, value, type = "text", onChange }: TextInputProps) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium">{label}</span>
      <input
        type={type}
        className="h-10 w-full rounded-md border bg-background px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function WorkflowBadge({ status }: { status: string }) {
  const variant: "success" | "destructive" | "warning" | "secondary" =
    status === "approved"
      ? "success"
      : status === "rejected"
        ? "destructive"
        : status === "reviewed"
          ? "warning"
          : "secondary";

  return <Badge variant={variant}>{status}</Badge>;
}
