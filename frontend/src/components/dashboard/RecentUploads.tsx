import { Badge } from "@/components/ui/badge";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import type { RecentUpload } from "@/data/dashboardData";

type RecentUploadsProps = {
  uploads: RecentUpload[];
};

const uploadStatusVariant = {
  Validated: "success",
  Processing: "warning",
  "Needs review": "destructive",
} as const;

export function RecentUploads({ uploads }: RecentUploadsProps) {
  return (
    <DashboardCard
      title="Recent uploads"
      description="Latest engineering files staged for analysis."
    >
      <div className="space-y-3">
        {uploads.map((upload) => (
          <div
            key={upload.id}
            className="flex flex-col gap-3 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="truncate text-sm font-medium">{upload.filename}</p>
                <Badge variant="outline">{upload.type}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Uploaded by {upload.uploadedBy} • {upload.uploadedAt}
              </p>
            </div>
            <Badge variant={uploadStatusVariant[upload.status]}>{upload.status}</Badge>
          </div>
        ))}
      </div>
    </DashboardCard>
  );
}
