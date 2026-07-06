import { API_BASE_URL } from "@/lib/apiBase";

export type User = {
  id: number;
  email: string;
  full_name: string | null;
};

type AuthResponse = {
  user: User;
};

type APIErrorResponse = {
  detail?: string;
  error?: {
    code?: string;
    message?: string;
  };
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new Error("API unavailable. Confirm the backend is running on http://localhost:8000.");
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as APIErrorResponse | null;
    throw new Error(
      payload?.error?.message ?? payload?.detail ?? "Authentication request failed.",
    );
  }

  return response.json() as Promise<T>;
}

export function registerUser(payload: {
  email: string;
  password: string;
  full_name?: string;
}) {
  return request<AuthResponse>("/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: { email: string; password: string }) {
  return request<AuthResponse>("/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logoutUser() {
  return request<{ status: string }>("/logout", {
    method: "POST",
  });
}

export function getCurrentUser() {
  return request<User>("/me");
}
