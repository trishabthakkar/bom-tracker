type APIErrorResponse = {
  detail?: string;
  error?: {
    message?: string;
  };
};

export async function getApiErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const payload = (await response.json().catch(() => null)) as APIErrorResponse | null;
  return payload?.error?.message ?? payload?.detail ?? fallback;
}
