const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type User = {
  id: number;
  email: string;
  full_name: string | null;
};

type AuthResponse = {
  user: User;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Authentication request failed.");
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
