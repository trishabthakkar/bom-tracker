import { useCallback, useEffect, useState } from "react";
import { AlertCircle, GitBranch, RefreshCw, Search } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getBomImports, type BomImport } from "@/lib/bomImportApi";
import {
  buildGraph,
  getAffectedChildren,
  getAffectedParents,
  getGraphStats,
  type GraphBuild,
  type GraphStats,
} from "@/lib/graphApi";

export function DependencyGraphPage() {
  const [bomImports, setBomImports] = useState<BomImport[]>([]);
  const [selectedUploadId, setSelectedUploadId] = useState("");
  const [graph, setGraph] = useState<GraphBuild | null>(null);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [partNumber, setPartNumber] = useState("PN-1212");
  const [parents, setParents] = useState<string[]>([]);
  const [children, setChildren] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [querying, setQuerying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadImports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const imports = await getBomImports();
      setBomImports(imports);
      const uploadId = selectedUploadId || String(imports[0]?.upload_id ?? "");
      setSelectedUploadId(uploadId);
      if (uploadId) {
        const [graphBuild, graphStats] = await Promise.all([
          buildGraph(Number(uploadId)),
          getGraphStats(Number(uploadId)),
        ]);
        setGraph(graphBuild);
        setStats(graphStats);
      }
    } catch (graphError) {
      setError(graphError instanceof Error ? graphError.message : "Unable to load graph data.");
    } finally {
      setLoading(false);
    }
  }, [selectedUploadId]);

  useEffect(() => {
    loadImports();
  }, [loadImports]);

  async function handleBuildGraph() {
    if (!selectedUploadId) {
      setError("Select a normalized BOM import first.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [graphBuild, graphStats] = await Promise.all([
        buildGraph(Number(selectedUploadId)),
        getGraphStats(Number(selectedUploadId)),
      ]);
      setGraph(graphBuild);
      setStats(graphStats);
      setParents([]);
      setChildren([]);
    } catch (graphError) {
      setError(graphError instanceof Error ? graphError.message : "Unable to build graph.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePartLookup() {
    if (!selectedUploadId || partNumber.trim().length === 0) {
      return;
    }

    setQuerying(true);
    setError(null);
    try {
      const [affectedParents, affectedChildren] = await Promise.all([
        getAffectedParents(Number(selectedUploadId), partNumber.trim()),
        getAffectedChildren(Number(selectedUploadId), partNumber.trim()),
      ]);
      setParents(affectedParents);
      setChildren(affectedChildren);
    } catch (lookupError) {
      setError(lookupError instanceof Error ? lookupError.message : "Unable to inspect part.");
    } finally {
      setQuerying(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Dependency graph</p>
          <h1 className="text-2xl font-semibold tracking-normal">Assembly relationships</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Build graph data from normalized BOM imports and inspect affected parents or children.
          </p>
        </div>
        <Button type="button" variant="outline" onClick={loadImports}>
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error ? (
        <div
          className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      <DashboardCard
        title="Graph source"
        description="Select a normalized BOM import to build graph data from the original upload."
      >
        <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
          <label className="space-y-2 text-sm">
            <span className="font-medium">Normalized BOM</span>
            <select
              className="h-10 w-full rounded-md border bg-background px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={selectedUploadId}
              onChange={(event) => setSelectedUploadId(event.target.value)}
            >
              <option value="">Select a BOM import</option>
              {bomImports.map((bomImport) => (
                <option key={bomImport.id} value={bomImport.upload_id}>
                  #{bomImport.id} {bomImport.filename} ({bomImport.row_count} rows)
                </option>
              ))}
            </select>
          </label>
          <Button type="button" disabled={loading || !selectedUploadId} onClick={handleBuildGraph}>
            <GitBranch className="h-4 w-4" />
            {loading ? "Loading..." : "Build graph"}
          </Button>
        </div>
      </DashboardCard>

      {stats ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard label="Nodes" value={stats.node_count} />
          <StatCard label="Edges" value={stats.edge_count} />
          <StatCard label="Roots" value={stats.root_count} />
          <StatCard label="Leaves" value={stats.leaf_count} />
          <DashboardCard title="Cycles">
            <Badge variant={stats.has_cycles ? "destructive" : "success"}>
              {stats.has_cycles ? "Detected" : "None"}
            </Badge>
          </DashboardCard>
        </section>
      ) : null}

      {graph ? (
        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <DashboardCard
            title="Part impact lookup"
            description="Find parent assemblies and downstream children for a part or assembly."
          >
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                className="h-10 flex-1 rounded-md border bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={partNumber}
                onChange={(event) => setPartNumber(event.target.value)}
                aria-label="Part number"
              />
              <Button type="button" disabled={querying} onClick={handlePartLookup}>
                <Search className="h-4 w-4" />
                {querying ? "Checking..." : "Inspect"}
              </Button>
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <NodeList title="Affected parents" nodes={parents} />
              <NodeList title="Affected children" nodes={children} />
            </div>
          </DashboardCard>

          <DashboardCard
            title="Graph edges"
            description={`${graph.filename} contains ${graph.edges.length} directed relationships.`}
          >
            <div className="max-h-96 overflow-auto rounded-md border">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2">Parent</th>
                    <th className="px-3 py-2">Child</th>
                  </tr>
                </thead>
                <tbody>
                  {graph.edges.map((edge) => (
                    <tr key={`${edge.source}-${edge.target}`} className="border-t">
                      <td className="px-3 py-2 font-medium">{edge.source}</td>
                      <td className="px-3 py-2 text-muted-foreground">{edge.target}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </DashboardCard>
        </section>
      ) : (
        <DashboardCard title="Graph data">
          <p className="text-sm text-muted-foreground">
            Import a BOM first, then select it here to build dependency graph data.
          </p>
        </DashboardCard>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <DashboardCard title={label}>
      <p className="text-3xl font-semibold tracking-normal">{value}</p>
    </DashboardCard>
  );
}

function NodeList({ title, nodes }: { title: string; nodes: string[] }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm font-medium">{title}</p>
      {nodes.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">No nodes found.</p>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          {nodes.map((node) => (
            <Badge key={node} variant="secondary">
              {node}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
