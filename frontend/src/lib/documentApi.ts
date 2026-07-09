import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";
import { csrfHeader } from "@/lib/csrf";

export type DocumentSection = {
  id: number;
  document_id: number;
  upload_id: number;
  section_index: number;
  heading: string;
  content: string;
  part_references: string[];
  created_at: string;
};

export type EngineeringDocument = {
  id: number;
  upload_id: number;
  filename: string;
  document_type: string;
  title: string | null;
  status: string;
  section_count: number;
  part_references: string[];
  created_at: string;
  archived_at: string | null;
};

export type EngineeringDocumentDetail = EngineeringDocument & {
  sections: DocumentSection[];
};

export async function indexDocumentUpload(uploadId: number): Promise<EngineeringDocumentDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/from-upload/${uploadId}`, {
    method: "POST",
    credentials: "include",
    headers: csrfHeader(),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to index document."));
  }

  return response.json() as Promise<EngineeringDocumentDetail>;
}

export async function getDocuments(): Promise<EngineeringDocument[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load documents."));
  }

  const payload = (await response.json()) as { documents: EngineeringDocument[] };
  return payload.documents;
}

export async function getDocument(documentId: number): Promise<EngineeringDocumentDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load document."));
  }

  return response.json() as Promise<EngineeringDocumentDetail>;
}
