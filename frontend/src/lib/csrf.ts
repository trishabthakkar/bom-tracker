export const CSRF_HEADER_NAME = "X-CSRF-Token";

export function getCsrfToken(): string | null {
  const cookies = document.cookie.split(";").map((cookie) => cookie.trim());
  const match = cookies.find((cookie) => cookie.startsWith("csrf_token="));
  if (!match) {
    return null;
  }

  return decodeURIComponent(match.slice("csrf_token=".length));
}

export function csrfHeader(): Record<string, string> {
  const token = getCsrfToken();
  return token ? { [CSRF_HEADER_NAME]: token } : {};
}
