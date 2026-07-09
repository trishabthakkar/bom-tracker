import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";
import { csrfHeader } from "@/lib/csrf";

export type SavedImpactReport = {
  id: number;
  bom_import_id: number;
  eco_record_id: number | null;
  graph_snapshot_id: number | null;
  bom_upload_id: number;
  summary: string;
  affected_part: string | null;
  effective_date: string | null;
  risk_level: string;
  risk_score: number;
  status: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
};

export type SavedImpactReportDetail = SavedImpactReport & {
  report: {
    summary: string;
    affected_part: string | null;
    effective_date: string | null;
    eco: {
      change_type: string | null;
      old_part: string | null;
      new_part: string | null;
      reason: string | null;
      effective_date: string | null;
      source: string;
      confidence: number;
    };
    affected_assemblies: Array<{
      part_number: string;
      affected_parents: string[];
      affected_children: string[];
      dependency_paths: string[][];
    }>;
    downstream_records: Array<{
      record_type: string;
      impact: string;
      severity: string;
    }>;
    affected_document_sections: Array<{
      document_id: number;
      document_title: string | null;
      filename: string;
      document_type: string;
      section_id: number;
      heading: string;
      matched_parts: string[];
      excerpt: string;
      severity: string;
    }>;
    suggested_updates: Array<{
      area: string;
      action: string;
      priority: string;
    }>;
    risk: {
      level: string;
      score: number;
      reasons: string[];
    };
  };
};

export async function getReports(): Promise<SavedImpactReport[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reports`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load reports."));
  }

  const payload = (await response.json()) as { reports: SavedImpactReport[] };
  return payload.reports;
}

export async function getReport(reportId: string): Promise<SavedImpactReportDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reports/${reportId}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load report."));
  }

  return response.json() as Promise<SavedImpactReportDetail>;
}

export async function createImpactReport({
  bomUploadId,
  ecoText,
}: {
  bomUploadId: number;
  ecoText: string;
}): Promise<SavedImpactReportDetail> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reports/impact-report`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
    },
    body: JSON.stringify({
      bom_upload_id: bomUploadId,
      eco_text: ecoText,
    }),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to generate impact report."));
  }

  return response.json() as Promise<SavedImpactReportDetail>;
}
