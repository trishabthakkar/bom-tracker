import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";
import { csrfHeader } from "@/lib/csrf";

export type GraphEdge = {
  source: string;
  target: string;
};

export type GraphBuild = {
  upload_id: number;
  filename: string;
  nodes: string[];
  edges: GraphEdge[];
};

export type GraphStats = {
  upload_id: number;
  node_count: number;
  edge_count: number;
  root_count: number;
  leaf_count: number;
  has_cycles: boolean;
};

export async function buildGraph(uploadId: number): Promise<GraphBuild> {
  const response = await fetch(`${API_BASE_URL}/api/v1/graph/build/${uploadId}`, {
    method: "POST",
    credentials: "include",
    headers: csrfHeader(),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to build dependency graph."));
  }

  return response.json() as Promise<GraphBuild>;
}

export async function getGraphStats(uploadId: number): Promise<GraphStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/graph/${uploadId}/stats`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load graph statistics."));
  }

  return response.json() as Promise<GraphStats>;
}

export async function getAffectedParents(uploadId: number, partNumber: string): Promise<string[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/graph/${uploadId}/parents/${encodeURIComponent(partNumber)}`,
    { credentials: "include" },
  );

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load affected parents."));
  }

  const payload = (await response.json()) as { nodes: string[] };
  return payload.nodes;
}

export async function getAffectedChildren(uploadId: number, partNumber: string): Promise<string[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/graph/${uploadId}/children/${encodeURIComponent(partNumber)}`,
    { credentials: "include" },
  );

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load affected children."));
  }

  const payload = (await response.json()) as { nodes: string[] };
  return payload.nodes;
}
