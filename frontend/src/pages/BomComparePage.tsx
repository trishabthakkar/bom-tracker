import { useCallback, useEffect, useState } from "react";
import { AlertCircle, GitCompare, RefreshCw } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  compareBomImports,
  getBomImports,
  type BomDiff,
  type BomImport,
} from "@/lib/bomImportApi";

export function BomComparePage() {
  const [imports, setImports] = useState<BomImport[]>([]);
  const [baseImportId, setBaseImportId] = useState("");
  const [targetImportId, setTargetImportId] = useState("");
  const [diff, setDiff] = useState<BomDiff | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshImports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const savedImports = await getBomImports();
      setImports(savedImports);
      setBaseImportId((current) => current || String(savedImports[1]?.id ?? savedImports[0]?.id ?? ""));
      setTargetImportId((current) => current || String(savedImports[0]?.id ?? ""));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load BOM imports.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshImports();
  }, [refreshImports]);

  async function handleCompare() {
    setComparing(true);
    setError(null);
    try {
      setDiff(await compareBomImports(Number(baseImportId), Number(targetImportId)));
    } catch (compareError) {
      setError(compareError instanceof Error ? compareError.message : "Unable to compare BOM imports.");
    } finally {
      setComparing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">BOM Versions</p>
          <h1 className="text-2xl font-semibold tracking-normal">Compare BOM imports</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Compare two normalized BOMs to identify added, removed, revised, and likely replaced parts.
          </p>
        </div>
        <Button type="button" variant="outline" onClick={refreshImports}>
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      <DashboardCard title="Select versions" description="Choose a base BOM and the newer target BOM.">
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
          <ImportSelect
            label="Base import"
            value={baseImportId}
            imports={imports}
            onChange={setBaseImportId}
          />
          <ImportSelect
            label="Target import"
            value={targetImportId}
            imports={imports}
            onChange={setTargetImportId}
          />
          <Button
            type="button"
            disabled={
              loading ||
              comparing ||
              !Number(baseImportId) ||
              !Number(targetImportId) ||
              baseImportId === targetImportId
            }
            onClick={handleCompare}
          >
            <GitCompare className="h-4 w-4" />
            {comparing ? "Comparing..." : "Compare"}
          </Button>
        </div>
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
        <DashboardCard title="Comparison">
          <p className="text-sm text-muted-foreground">Loading imports...</p>
        </DashboardCard>
      ) : imports.length < 2 ? (
        <DashboardCard title="Comparison">
          <p className="text-sm text-muted-foreground">
            Upload and import at least two BOM files to compare versions.
          </p>
        </DashboardCard>
      ) : diff ? (
        <ComparisonResults diff={diff} />
      ) : (
        <DashboardCard title="Comparison">
          <p className="text-sm text-muted-foreground">Select two imports and run a comparison.</p>
        </DashboardCard>
      )}
    </div>
  );
}

type ImportSelectProps = {
  label: string;
  value: string;
  imports: BomImport[];
  onChange: (value: string) => void;
};

function ImportSelect({ label, value, imports, onChange }: ImportSelectProps) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium">{label}</span>
      <select
        className="h-10 w-full rounded-md border bg-background px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">Select an import</option>
        {imports.map((bomImport) => (
          <option key={bomImport.id} value={bomImport.id}>
            #{bomImport.id} {bomImport.version_label ?? ""} {bomImport.filename} ({bomImport.row_count} rows)
          </option>
        ))}
      </select>
    </label>
  );
}

function ComparisonResults({ diff }: { diff: BomDiff }) {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Added" value={diff.summary.added_count} />
        <MetricCard label="Removed" value={diff.summary.removed_count} />
        <MetricCard label="Revised" value={diff.summary.revised_count} />
        <MetricCard label="Replacements" value={diff.summary.replacement_candidate_count} />
        <MetricCard label="Unchanged" value={diff.summary.unchanged_count} />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <PartList title="Added parts" parts={diff.added_parts} empty="No added parts." />
        <PartList title="Removed parts" parts={diff.removed_parts} empty="No removed parts." />
      </section>

      <DashboardCard title="Revised parts">
        {diff.revised_parts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No revised parts.</p>
        ) : (
          <div className="space-y-3">
            {diff.revised_parts.map((part) => (
              <div key={part.part_number} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{part.part_number}</p>
                <p className="mt-1 text-muted-foreground">
                  Revision: {part.base_revision ?? "-"} to {part.target_revision ?? "-"}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {part.description_changed ? <Badge variant="warning">description</Badge> : null}
                  {part.parent_changed ? <Badge variant="warning">parent</Badge> : null}
                  {part.child_changed ? <Badge variant="warning">child</Badge> : null}
                </div>
              </div>
            ))}
          </div>
        )}
      </DashboardCard>

      <DashboardCard title="Possible replacements">
        {diff.replacement_candidates.length === 0 ? (
          <p className="text-sm text-muted-foreground">No likely replacement pairs found.</p>
        ) : (
          <div className="space-y-3">
            {diff.replacement_candidates.map((candidate) => (
              <div
                key={`${candidate.removed_part.part_number}-${candidate.added_part.part_number}`}
                className="rounded-md border p-3 text-sm"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <p className="font-medium">
                    {candidate.removed_part.part_number} to {candidate.added_part.part_number}
                  </p>
                  <Badge variant="secondary">{Math.round(candidate.confidence * 100)}% match</Badge>
                </div>
                <p className="mt-1 text-muted-foreground">{candidate.reason}</p>
              </div>
            ))}
          </div>
        )}
      </DashboardCard>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <DashboardCard title={label}>
      <p className="text-2xl font-semibold">{value}</p>
    </DashboardCard>
  );
}

function PartList({
  title,
  parts,
  empty,
}: {
  title: string;
  parts: BomDiff["added_parts"];
  empty: string;
}) {
  return (
    <DashboardCard title={title}>
      {parts.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <div className="max-h-96 space-y-3 overflow-auto pr-1">
          {parts.map((part) => (
            <div key={part.part_number} className="rounded-md border p-3 text-sm">
              <p className="font-medium">{part.part_number}</p>
              <p className="mt-1 text-muted-foreground">{part.description ?? "No description"}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Parent: {part.parent_assembly ?? "-"} • Child: {part.child_assembly ?? "-"} • Rev:{" "}
                {part.revision ?? "-"}
              </p>
            </div>
          ))}
        </div>
      )}
    </DashboardCard>
  );
}
