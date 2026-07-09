import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";
import { csrfHeader } from "@/lib/csrf";

export type EcoRecord = {
  id: number;
  upload_id: number | null;
  source_type: string;
  change_type: string | null;
  old_part: string | null;
  new_part: string | null;
  reason: string | null;
  effective_date: string | null;
  parser_source: string;
  confidence: number;
  workflow_status: string;
  correction_notes: string | null;
  approval_notes: string | null;
  reviewed_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  created_at: string;
};

export type EcoRecordDetail = EcoRecord & {
  source_text: string | null;
  parsed: {
    change_type: string | null;
    old_part: string | null;
    new_part: string | null;
    reason: string | null;
    effective_date: string | null;
    source: string;
    confidence: number;
  };
};

export async function saveEcoText(text: string): Promise<EcoRecordDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/eco-records/parse-text`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to save ECO record."));
  }

  return response.json() as Promise<EcoRecordDetail>;
}

export async function saveEcoUpload(uploadId: number): Promise<EcoRecordDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/eco-records/parse-upload/${uploadId}`, {
    method: "POST",
    credentials: "include",
    headers: csrfHeader(),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to save ECO upload."));
  }

  return response.json() as Promise<EcoRecordDetail>;
}

export async function getEcoRecords(): Promise<EcoRecord[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/eco-records`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load ECO records."));
  }

  const payload = (await response.json()) as { records: EcoRecord[] };
  return payload.records;
}

export async function getEcoRecord(recordId: number): Promise<EcoRecordDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/eco-records/${recordId}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load ECO record."));
  }

  return response.json() as Promise<EcoRecordDetail>;
}

export type EcoRecordUpdate = {
  change_type: string | null;
  old_part: string | null;
  new_part: string | null;
  reason: string | null;
  effective_date: string | null;
  correction_notes: string | null;
};

export async function updateEcoRecord(
  recordId: number,
  payload: EcoRecordUpdate,
): Promise<EcoRecordDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/eco-records/${recordId}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to update ECO record."));
  }

  return response.json() as Promise<EcoRecordDetail>;
}

export async function transitionEcoRecord(
  recordId: number,
  action: "review" | "approve" | "reject",
  notes: string | null = null,
): Promise<EcoRecordDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/eco-records/${recordId}/${action}`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({ notes }),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, `Unable to ${action} ECO record.`));
  }

  return response.json() as Promise<EcoRecordDetail>;
}
