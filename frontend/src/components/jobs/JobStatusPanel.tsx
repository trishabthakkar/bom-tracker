import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Job } from "@/lib/jobApi";

type JobStatusPanelProps = {
  job: Job | null;
  title?: string;
};

export function JobStatusPanel({ job, title = "Background job" }: JobStatusPanelProps) {
  if (!job) {
    return null;
  }

  const complete = job.status === "completed";
  const failed = job.status === "failed";

  return (
    <div
      className="rounded-md border bg-muted/20 p-3"
      role={failed ? "alert" : "status"}
      aria-live="polite"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 gap-3">
          <span className="mt-0.5 shrink-0">
            {failed ? (
              <AlertCircle className="h-4 w-4 text-destructive" />
            ) : complete ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            )}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium">
              {title} #{job.id}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {job.error_message ?? job.status_message ?? formatJobType(job.job_type)}
            </p>
          </div>
        </div>
        <Badge variant={failed ? "destructive" : complete ? "success" : "secondary"}>
          {job.status}
        </Badge>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={
            failed
              ? "h-full bg-destructive transition-all"
              : complete
                ? "h-full bg-emerald-600 transition-all"
                : "h-full bg-primary transition-all"
          }
          style={{ width: `${Math.max(5, Math.min(100, job.progress_percent))}%` }}
        />
      </div>
    </div>
  );
}

function formatJobType(value: string): string {
  return value.replace(/_/g, " ");
}
