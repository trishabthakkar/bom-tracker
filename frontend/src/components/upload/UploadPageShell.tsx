import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { FileDropzone } from "@/components/upload/FileDropzone";
import { UploadHistory } from "@/components/upload/UploadHistory";
import { UploadProgress } from "@/components/upload/UploadProgress";
import {
  getUploadHistory,
  uploadFile,
  type UploadCategory,
  type UploadedFile,
} from "@/lib/uploadApi";

type UploadPageShellProps = {
  title: string;
  description: string;
  category: UploadCategory;
  acceptedExtensions: string[];
  acceptedLabels: string[];
  maxSizeMb?: number;
};

export function UploadPageShell({
  title,
  description,
  category,
  acceptedExtensions,
  acceptedLabels,
  maxSizeMb = 25,
}: UploadPageShellProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploads, setUploads] = useState<UploadedFile[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const accept = useMemo(() => acceptedExtensions.join(","), [acceptedExtensions]);

  const refreshHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const history = await getUploadHistory();
      setUploads(history.filter((upload) => upload.upload_category === category));
    } catch {
      setUploads([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [category]);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  function handleFileSelected(file: File) {
    setMessage(null);
    setError(null);
    setProgress(0);

    const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
    if (!acceptedExtensions.includes(extension)) {
      setSelectedFile(null);
      setError(`Unsupported file type. Accepted: ${acceptedLabels.join(", ")}.`);
      return;
    }

    if (file.size > maxSizeMb * 1024 * 1024) {
      setSelectedFile(null);
      setError(`File exceeds the ${maxSizeMb} MB upload limit.`);
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError("Select a file before uploading.");
      return;
    }

    setUploading(true);
    setError(null);
    setMessage(null);
    setProgress(0);

    try {
      const uploaded = await uploadFile({
        file: selectedFile,
        category,
        onProgress: setProgress,
      });
      setMessage(`${uploaded.original_filename} uploaded successfully.`);
      setSelectedFile(null);
      await refreshHistory();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Secure upload</p>
          <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p>
        </div>
        <Badge variant="secondary">Max {maxSizeMb} MB</Badge>
      </div>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <DashboardCard
          title="Upload file"
          description="Files are validated and stored for future parsing workflows."
        >
          <div className="space-y-4">
            <FileDropzone
              accept={accept}
              acceptedLabels={acceptedLabels}
              maxSizeMb={maxSizeMb}
              disabled={uploading}
              onFileSelected={handleFileSelected}
            />

            {selectedFile ? (
              <div className="rounded-md border bg-muted/30 p-3">
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            ) : null}

            {uploading ? <UploadProgress progress={progress} /> : null}

            {message ? (
              <div
                className="flex gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"
                role="status"
                aria-live="polite"
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{message}</span>
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

            <Button
              type="button"
              className="w-full"
              disabled={!selectedFile || uploading}
              onClick={handleUpload}
            >
              {uploading ? "Uploading..." : "Upload securely"}
            </Button>
          </div>
        </DashboardCard>

        <UploadHistory uploads={uploads} loading={historyLoading} />
      </section>
    </div>
  );
}

function formatFileSize(sizeBytes: number) {
  if (sizeBytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(sizeBytes / 1024))} KB`;
  }

  return `${(sizeBytes / 1024 / 1024).toFixed(1)} MB`;
}
