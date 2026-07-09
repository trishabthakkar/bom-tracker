import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, AlertCircle, Download, MessageSquare, Save } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { RiskBadge } from "@/components/reports/RiskBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  addReportComment,
  getReport,
  reportExportUrl,
  updateReportReview,
  type SavedImpactReportDetail,
} from "@/lib/reportApi";

export function ReportDetailPage() {
  const { reportId } = useParams();
  const [report, setReport] = useState<SavedImpactReportDetail | null>(null);
  const [reviewStatus, setReviewStatus] = useState("draft");
  const [signoffNotes, setSignoffNotes] = useState("");
  const [commentBody, setCommentBody] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) {
      setError("Report id is missing.");
      setLoading(false);
      return;
    }

    getReport(reportId)
      .then((loadedReport) => {
        setReport(loadedReport);
        setReviewStatus(loadedReport.review_status);
        setSignoffNotes(loadedReport.signoff_notes ?? "");
      })
      .catch((reportError) => {
        setError(reportError instanceof Error ? reportError.message : "Unable to load report.");
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  async function handleSaveReview() {
    if (!report) {
      return;
    }

    setSaving(true);
    setActionError(null);
    try {
      const updated = await updateReportReview({
        reportId: report.id,
        reviewStatus,
        assignedUserId: report.assigned_user_id,
        signoffNotes,
      });
      setReport(updated);
      setReviewStatus(updated.review_status);
      setSignoffNotes(updated.signoff_notes ?? "");
    } catch (reviewError) {
      setActionError(reviewError instanceof Error ? reviewError.message : "Unable to update report review status.");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddComment() {
    if (!report || commentBody.trim().length === 0) {
      return;
    }

    setSaving(true);
    setActionError(null);
    try {
      await addReportComment(report.id, commentBody);
      const updated = await getReport(String(report.id));
      setReport(updated);
      setCommentBody("");
    } catch (commentError) {
      setActionError(commentError instanceof Error ? commentError.message : "Unable to add report comment.");
    } finally {
      setSaving(false);
    }
  }

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
        <div className="flex flex-wrap items-center gap-2">
          <Button asChild variant="outline" size="sm">
            <a href={reportExportUrl(report.id, "csv")}>
              <Download className="h-4 w-4" />
              CSV
            </a>
          </Button>
          <Button asChild variant="outline" size="sm">
            <a href={reportExportUrl(report.id, "pdf")}>
              <Download className="h-4 w-4" />
              PDF
            </a>
          </Button>
          <RiskBadge level={report.risk_level} />
        </div>
      </div>

      <section className="grid gap-4 lg:grid-cols-4">
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
        <DashboardCard title="Review">
          <ReviewStatusBadge status={report.review_status} />
          <p className="mt-2 text-sm text-muted-foreground">
            Signed off: {report.signed_off_at ? new Date(report.signed_off_at).toLocaleString() : "-"}
          </p>
        </DashboardCard>
      </section>

      {actionError ? (
        <div
          className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      ) : null}

      <DashboardCard title="Review workflow" description="Track report review, change requests, and sign-off.">
        <div className="grid gap-4 lg:grid-cols-[240px_1fr_auto] lg:items-end">
          <label className="space-y-2 text-sm">
            <span className="font-medium">Review status</span>
            <select
              className="h-10 w-full rounded-md border bg-background px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={reviewStatus}
              onChange={(event) => setReviewStatus(event.target.value)}
            >
              <option value="draft">Draft</option>
              <option value="in_review">In review</option>
              <option value="changes_requested">Changes requested</option>
              <option value="signed_off">Signed off</option>
            </select>
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium">Notes</span>
            <textarea
              className="min-h-20 w-full rounded-md border bg-background p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={signoffNotes}
              onChange={(event) => setSignoffNotes(event.target.value)}
            />
          </label>
          <Button type="button" disabled={saving} onClick={handleSaveReview}>
            <Save className="h-4 w-4" />
            Save
          </Button>
        </div>
      </DashboardCard>

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

      <DashboardCard title="Affected document sections">
        {report.report.affected_document_sections.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No indexed document sections referenced the affected part.
          </p>
        ) : (
          <div className="space-y-3">
            {report.report.affected_document_sections.map((section) => (
              <div key={section.section_id} className="rounded-md border p-3 text-sm">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="font-medium">{section.heading}</p>
                    <p className="mt-1 text-muted-foreground">
                      {section.document_title ?? section.filename} •{" "}
                      {section.document_type.replace(/_/g, " ")}
                    </p>
                  </div>
                  <RiskBadge level={section.severity} />
                </div>
                <p className="mt-2 text-muted-foreground">{section.excerpt}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Matched parts: {section.matched_parts.join(", ")}
                </p>
              </div>
            ))}
          </div>
        )}
      </DashboardCard>

      <DashboardCard title="Comments" description="Capture review notes and collaboration context.">
        <div className="space-y-4">
          <label className="space-y-2 text-sm">
            <span className="font-medium">New comment</span>
            <textarea
              className="min-h-20 w-full rounded-md border bg-background p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={commentBody}
              onChange={(event) => setCommentBody(event.target.value)}
            />
          </label>
          <Button type="button" disabled={saving || commentBody.trim().length === 0} onClick={handleAddComment}>
            <MessageSquare className="h-4 w-4" />
            Add comment
          </Button>
          {report.comments.length === 0 ? (
            <p className="text-sm text-muted-foreground">No comments yet.</p>
          ) : (
            <div className="space-y-3">
              {report.comments.map((comment) => (
                <div key={comment.id} className="rounded-md border p-3 text-sm">
                  <p className="text-muted-foreground">
                    User #{comment.user_id} • {new Date(comment.created_at).toLocaleString()}
                  </p>
                  <p className="mt-2">{comment.body}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </DashboardCard>
    </div>
  );
}

function ReviewStatusBadge({ status }: { status: string }) {
  const variant: "secondary" | "warning" | "success" | "destructive" =
    status === "signed_off"
      ? "success"
      : status === "changes_requested"
        ? "destructive"
        : status === "in_review"
          ? "warning"
          : "secondary";

  return <Badge variant={variant}>{status.replace(/_/g, " ")}</Badge>;
}
