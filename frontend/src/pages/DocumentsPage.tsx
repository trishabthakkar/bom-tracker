import { useCallback, useEffect, useState } from "react";
import { AlertCircle, FileText, RefreshCw } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UploadPageShell } from "@/components/upload/UploadPageShell";
import {
  getDocument,
  getDocuments,
  indexDocumentUpload,
  type EngineeringDocument,
  type EngineeringDocumentDetail,
} from "@/lib/documentApi";
import type { UploadedFile } from "@/lib/uploadApi";

export function DocumentsPage() {
  const [documents, setDocuments] = useState<EngineeringDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<EngineeringDocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
    setLoading(true);
    try {
      setDocuments(await getDocuments());
    } catch (documentError) {
      setError(documentError instanceof Error ? documentError.message : "Unable to load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  async function handleUploadComplete(upload: UploadedFile) {
    setIndexing(true);
    setError(null);
    setMessage(null);

    try {
      const indexed = await indexDocumentUpload(upload.id);
      setSelectedDocument(indexed);
      setMessage(`Indexed ${indexed.section_count} sections from ${indexed.filename}.`);
      await refreshDocuments();
    } catch (indexError) {
      setError(indexError instanceof Error ? indexError.message : "Unable to index document.");
    } finally {
      setIndexing(false);
    }
  }

  async function handleOpenDocument(documentId: number) {
    setError(null);
    try {
      setSelectedDocument(await getDocument(documentId));
    } catch (documentError) {
      setError(documentError instanceof Error ? documentError.message : "Unable to open document.");
    }
  }

  return (
    <div className="space-y-6">
      <UploadPageShell
        title="Engineering Documents"
        description="Upload installation guides, commissioning procedures, service manuals, or procurement PDFs for downstream impact matching."
        category="document"
        acceptedExtensions={[".pdf"]}
        acceptedLabels={["PDF"]}
        onUploadComplete={handleUploadComplete}
      />

      {indexing ? (
        <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
          Indexing document text, sections, and part references...
        </div>
      ) : null}

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

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <DashboardCard
          title="Indexed documents"
          description="Documents available for report-level downstream section matching."
          action={
            <Button type="button" size="sm" variant="outline" onClick={refreshDocuments}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          }
        >
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading documents...</p>
          ) : documents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No indexed documents yet.</p>
          ) : (
            <div className="space-y-3">
              {documents.map((document) => (
                <button
                  key={document.id}
                  type="button"
                  className="w-full rounded-md border p-3 text-left transition-colors hover:bg-muted/40"
                  onClick={() => handleOpenDocument(document.id)}
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{document.title ?? document.filename}</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {document.section_count} sections • {document.part_references.length} part refs
                      </p>
                    </div>
                    <Badge variant="secondary">{formatDocumentType(document.document_type)}</Badge>
                  </div>
                </button>
              ))}
            </div>
          )}
        </DashboardCard>

        <DashboardCard title="Document sections" description="Detected sections and part references.">
          {selectedDocument ? (
            <div className="space-y-4">
              <div className="rounded-md border p-3">
                <div className="flex items-start gap-3">
                  <FileText className="mt-0.5 h-4 w-4 text-primary" />
                  <div>
                    <p className="font-medium">{selectedDocument.title ?? selectedDocument.filename}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {selectedDocument.filename} • {formatDocumentType(selectedDocument.document_type)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="max-h-[34rem] space-y-3 overflow-auto pr-1">
                {selectedDocument.sections.map((section) => (
                  <div key={section.id} className="rounded-md border p-3 text-sm">
                    <p className="font-medium">{section.heading}</p>
                    <p className="mt-2 line-clamp-4 text-muted-foreground">{section.content}</p>
                    {section.part_references.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {section.part_references.map((part) => (
                          <Badge key={part} variant="outline">
                            {part}
                          </Badge>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Select an indexed document to inspect its extracted sections.
            </p>
          )}
        </DashboardCard>
      </section>
    </div>
  );
}

function formatDocumentType(value: string) {
  return value.replace(/_/g, " ");
}
