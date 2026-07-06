import { useCallback, useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UploadPageShell } from "@/components/upload/UploadPageShell";
import {
  getBomImports,
  importBomUpload,
  type BomImport,
  type BomImportDetail,
} from "@/lib/bomImportApi";
import type { UploadedFile } from "@/lib/uploadApi";

export function UploadBomPage() {
  const [imports, setImports] = useState<BomImport[]>([]);
  const [latestImport, setLatestImport] = useState<BomImportDetail | null>(null);
  const [loadingImports, setLoadingImports] = useState(true);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);

  const refreshImports = useCallback(async () => {
    setLoadingImports(true);
    try {
      setImports(await getBomImports());
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "Unable to load BOM imports.");
    } finally {
      setLoadingImports(false);
    }
  }, []);

  useEffect(() => {
    refreshImports();
  }, [refreshImports]);

  async function handleUploadComplete(upload: UploadedFile) {
    setImporting(true);
    setImportError(null);

    try {
      const imported = await importBomUpload(upload.id);
      setLatestImport(imported);
      await refreshImports();
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "Unable to import BOM.");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="space-y-6">
      <UploadPageShell
        title="Upload BOM"
        description="Upload CSV or Excel BOM files so the system can normalize assemblies, parts, and dependencies."
        category="bom"
        acceptedExtensions={[".csv", ".xlsx"]}
        acceptedLabels={["CSV", "XLSX"]}
        onUploadComplete={handleUploadComplete}
      />

      {importing ? (
        <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
          Importing BOM rows and dependency graph...
        </div>
      ) : null}

      {importError ? (
        <div
          className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{importError}</span>
        </div>
      ) : null}

      {latestImport ? (
        <DashboardCard
          title="Latest normalized BOM"
          description="The uploaded BOM was parsed and persisted for graph/report workflows."
        >
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <p className="text-muted-foreground">Import</p>
              <p className="font-medium">#{latestImport.id}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Rows</p>
              <p className="font-medium">{latestImport.row_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Relationships</p>
              <p className="font-medium">{latestImport.relationships.length}</p>
            </div>
          </div>
          <div className="mt-4 max-h-72 overflow-auto rounded-md border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">Part</th>
                  <th className="px-3 py-2">Description</th>
                  <th className="px-3 py-2">Parent</th>
                  <th className="px-3 py-2">Revision</th>
                </tr>
              </thead>
              <tbody>
                {latestImport.parts.slice(0, 8).map((part) => (
                  <tr key={part.id} className="border-t">
                    <td className="px-3 py-2 font-medium">{part.part_number}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {part.description ?? "-"}
                    </td>
                    <td className="px-3 py-2">{part.parent_assembly ?? "-"}</td>
                    <td className="px-3 py-2">{part.revision ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DashboardCard>
      ) : null}

      <DashboardCard
        title="Saved BOM imports"
        description="Persisted normalized BOM batches available for downstream analysis."
        action={
          <Button type="button" size="sm" variant="outline" onClick={refreshImports}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      >
        {loadingImports ? (
          <p className="text-sm text-muted-foreground">Loading imports...</p>
        ) : imports.length === 0 ? (
          <p className="text-sm text-muted-foreground">No normalized BOM imports yet.</p>
        ) : (
          <div className="space-y-3">
            {imports.map((bomImport) => (
              <div
                key={bomImport.id}
                className="flex flex-col gap-2 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium">{bomImport.filename}</p>
                  <p className="text-sm text-muted-foreground">
                    Import #{bomImport.id} • {bomImport.row_count} rows •{" "}
                    {new Date(bomImport.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="success">
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                    {bomImport.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </DashboardCard>
    </div>
  );
}
