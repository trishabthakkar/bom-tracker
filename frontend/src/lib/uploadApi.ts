import { API_BASE_URL } from "@/lib/apiBase";

export type UploadCategory = "bom" | "eco" | "document";

export type UploadedFile = {
  id: number;
  original_filename: string;
  stored_filename: string;
  file_extension: string;
  content_type: string;
  size_bytes: number;
  upload_category: UploadCategory;
  status: string;
  created_at: string;
};

export type UploadListResponse = {
  uploads: UploadedFile[];
};

export function uploadFile({
  file,
  category,
  replaceExisting = false,
  onProgress,
}: {
  file: File;
  category: UploadCategory;
  replaceExisting?: boolean;
  onProgress: (progress: number) => void;
}): Promise<UploadedFile> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    const formData = new FormData();

    formData.append("file", file);
    formData.append("upload_category", category);
    formData.append("replace_existing", String(replaceExisting));

    request.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    request.onload = () => {
      const payload = parseJson(request.responseText);

      if (request.status >= 200 && request.status < 300) {
        onProgress(100);
        resolve(payload as UploadedFile);
        return;
      }

      reject(new Error(getErrorMessage(payload)));
    };

    request.onerror = () => reject(new Error("Upload failed. Check your connection."));
    request.withCredentials = true;
    request.open("POST", `${API_BASE_URL}/api/v1/uploads`);
    request.send(formData);
  });
}

export async function getUploadHistory(): Promise<UploadedFile[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/uploads`, {
    credentials: "include",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    throw new Error(getErrorMessage(payload));
  }

  const payload = (await response.json()) as UploadListResponse;
  return payload.uploads;
}

function parseJson(value: string): unknown {
  try {
    return JSON.parse(value) as unknown;
  } catch {
    return null;
  }
}

function getErrorMessage(payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "error" in payload &&
    payload.error &&
    typeof payload.error === "object" &&
    "message" in payload.error &&
    typeof payload.error.message === "string"
  ) {
    return payload.error.message;
  }

  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }

  return "Upload request failed.";
}
