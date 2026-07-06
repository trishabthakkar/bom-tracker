import { FileSpreadsheet, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import type { UploadedFile } from "@/lib/uploadApi";

type UploadHistoryProps = {
  uploads: UploadedFile[];
  loading: boolean;
};

export function UploadHistory({ uploads, loading }: UploadHistoryProps) {
  return (
    <DashboardCard
      title="Upload history"
      description="Stored files available for future parsing modules."
    >
      {loading ? (
        <p className="text-sm text-muted-foreground">Loading upload history...</p>
      ) : uploads.length === 0 ? (
        <p className="text-sm text-muted-foreground">No uploads yet.</p>
      ) : (
        <div className="space-y-3">
          {uploads.map((upload) => {
            const Icon = upload.file_extension === ".pdf" ? FileText : FileSpreadsheet;

            return (
              <div
                key={upload.id}
                className="flex flex-col gap-3 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex min-w-0 gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-muted">
                    <Icon className="h-5 w-5 text-primary" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{upload.original_filename}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatFileSize(upload.size_bytes)} • {formatDate(upload.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Badge variant="outline">{upload.upload_category.toUpperCase()}</Badge>
                  <Badge variant="success">{upload.status}</Badge>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </DashboardCard>
  );
}

function formatFileSize(sizeBytes: number) {
  if (sizeBytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  }

  return `${(sizeBytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
