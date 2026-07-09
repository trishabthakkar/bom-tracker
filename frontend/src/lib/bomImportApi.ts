import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";

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
  row_count: number;
  status: string;
  created_at: string;
  archived_at: string | null;
};

export type BomImportDetail = BomImport & {
  parts: BomPart[];
  relationships: AssemblyRelationship[];
};

export async function importBomUpload(uploadId: number): Promise<BomImportDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bom-imports/from-upload/${uploadId}`, {
    method: "POST",
    credentials: "include",
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
