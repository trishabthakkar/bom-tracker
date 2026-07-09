import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";
import { csrfHeader } from "@/lib/csrf";

export type BomPart = {
  id: number;
  row_number: number;
  part_number: string;
  description: string | null;
  parent_assembly: string | null;
  child_assembly: string | null;
  revision: string | null;
};

export type AssemblyRelationship = {
  id: number;
  parent_part_number: string;
  child_part_number: string;
  relationship_type: string;
};

export type BomImport = {
  id: number;
  upload_id: number;
  filename: string;
  version_label: string | null;
  previous_import_id: number | null;
  import_notes: string | null;
  row_count: number;
  status: string;
  created_at: string;
  archived_at: string | null;
};

export type BomImportDetail = BomImport & {
  parts: BomPart[];
  relationships: AssemblyRelationship[];
};

export type BomRevisionChange = {
  part_number: string;
  base_revision: string | null;
  target_revision: string | null;
  description_changed: boolean;
  parent_changed: boolean;
  child_changed: boolean;
};

export type BomReplacementCandidate = {
  removed_part: Omit<BomPart, "id" | "row_number">;
  added_part: Omit<BomPart, "id" | "row_number">;
  confidence: number;
  reason: string;
};

export type BomDiff = {
  base_import: BomImport;
  target_import: BomImport;
  summary: {
    added_count: number;
    removed_count: number;
    revised_count: number;
    replacement_candidate_count: number;
    unchanged_count: number;
  };
  added_parts: Array<Omit<BomPart, "id" | "row_number">>;
  removed_parts: Array<Omit<BomPart, "id" | "row_number">>;
  revised_parts: BomRevisionChange[];
  replacement_candidates: BomReplacementCandidate[];
};

export async function importBomUpload(uploadId: number): Promise<BomImportDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bom-imports/from-upload/${uploadId}`, {
    method: "POST",
    credentials: "include",
    headers: csrfHeader(),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to import BOM."));
  }

  return response.json() as Promise<BomImportDetail>;
}

export async function getBomImports(): Promise<BomImport[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bom-imports`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load BOM imports."));
  }

  const payload = (await response.json()) as { imports: BomImport[] };
  return payload.imports;
}

export async function getBomImport(importId: number): Promise<BomImportDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bom-imports/${importId}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load BOM import."));
  }

  return response.json() as Promise<BomImportDetail>;
}

export async function compareBomImports(baseImportId: number, targetImportId: number): Promise<BomDiff> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bom-imports/diff`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({
      base_import_id: baseImportId,
      target_import_id: targetImportId,
    }),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to compare BOM imports."));
  }

  return response.json() as Promise<BomDiff>;
}
