import { API_BASE_URL } from "@/lib/apiBase";
import { getApiErrorMessage } from "@/lib/apiErrors";
import { csrfHeader } from "@/lib/csrf";

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export type Job = {
  id: number;
  job_type: string;
  status: JobStatus;
  progress_percent: number;
  status_message: string | null;
  entity_type: string | null;
  entity_id: number | null;
  input_json: Record<string, unknown>;
  result_json: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export async function startBomImportJob(uploadId: number): Promise<Job> {
  return startJob(`/api/v1/jobs/bom-imports/from-upload/${uploadId}`, "Unable to queue BOM import.");
}

export async function startEcoUploadParseJob(uploadId: number): Promise<Job> {
  return startJob(`/api/v1/jobs/eco-records/parse-upload/${uploadId}`, "Unable to queue ECO parsing.");
}

export async function startGraphBuildJob(uploadId: number): Promise<Job> {
  return startJob(`/api/v1/jobs/graph/build/${uploadId}`, "Unable to queue graph build.");
}

export async function startImpactReportJob({
  bomUploadId,
  ecoText,
}: {
  bomUploadId: number;
  ecoText: string;
}): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/reports/impact-report`, {
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
    throw new Error(await getApiErrorMessage(response, "Unable to queue impact report."));
  }

  return response.json() as Promise<Job>;
}

export async function getJob(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Unable to load job status."));
  }

  return response.json() as Promise<Job>;
}

export async function pollJobUntilFinished(
  job: Job,
  onUpdate: (job: Job) => void,
  intervalMs = 1200,
): Promise<Job> {
  let current = job;
  onUpdate(current);

  while (current.status === "queued" || current.status === "processing") {
    await wait(intervalMs);
    current = await getJob(current.id);
    onUpdate(current);
  }

  return current;
}

async function startJob(path: string, fallback: string): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: csrfHeader(),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, fallback));
  }

  return response.json() as Promise<Job>;
}

function wait(durationMs: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, durationMs));
}
