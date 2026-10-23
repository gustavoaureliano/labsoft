export type ApiRole = "student" | "teacher" | "admin";

export type ApiLogin = {
  access_token: string;
  user: {
    id: string;
    email: string;
    role: ApiRole;
  };
};

export type ApiNotification = {
  id: string;
  category: string;
  message: string;
  details: Record<string, unknown>;
  created_at: string;
  read_at: string | null;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ?? "";
const accessTokenKey = "aprovaai-api-access-token";

export const isApiConfigured = apiBaseUrl.length > 0;

export function hasApiSession() {
  return window.sessionStorage.getItem(accessTokenKey) !== null;
}

function getAccessToken() {
  return window.sessionStorage.getItem(accessTokenKey);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body) headers.set("Content-Type", "application/json");

  const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
    const detail = payload?.detail;
    const message = typeof detail === "string" ? detail : `Falha na API (${response.status}).`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function loginWithApi(email: string, password: string) {
  const result = await request<ApiLogin>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  window.sessionStorage.setItem(accessTokenKey, result.access_token);
  return result.user;
}

export function clearApiSession() {
  window.sessionStorage.removeItem(accessTokenKey);
}

export async function logoutFromApi() {
  if (!getAccessToken()) return;
  await request<{ message: string }>("/api/v1/auth/logout", { method: "POST" });
  clearApiSession();
}

export function fetchNotifications() {
  return request<ApiNotification[]>("/api/v1/notifications/me");
}

export function markNotificationAsRead(notificationId: string) {
  return request<ApiNotification>(
    `/api/v1/notifications/${encodeURIComponent(notificationId)}/read`,
    { method: "PATCH" },
  );
}
