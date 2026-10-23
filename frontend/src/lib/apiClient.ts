export type ApiRole = "student" | "teacher" | "admin";

export type ApiUser = {
  id: string;
  email: string;
  role: ApiRole;
};

export type ApiLogin = {
  access_token: string;
  user: ApiUser;
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
let accessToken: string | null = null;
let refreshInFlight: Promise<boolean> | null = null;

export const isApiConfigured = apiBaseUrl.length > 0;

export function hasApiSession() {
  return accessToken !== null;
}

function shouldRefresh(path: string) {
  return ![
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
  ].some((endpoint) => path.startsWith(endpoint));
}

async function fetchApi(
  path: string,
  init: RequestInit,
  token: string | null,
) {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body) headers.set("Content-Type", "application/json");

  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
}

async function refreshAccessToken() {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetchApi(
          "/api/v1/auth/refresh",
          { method: "POST" },
          null,
        );
        if (!response.ok) {
          accessToken = null;
          return false;
        }
        const result = await response.json() as ApiLogin;
        accessToken = result.access_token;
        return true;
      } catch {
        accessToken = null;
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response = await fetchApi(path, init, accessToken);
  if (response.status === 401 && shouldRefresh(path)) {
    if (await refreshAccessToken()) {
      response = await fetchApi(path, init, accessToken);
    }
  }
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
  accessToken = result.access_token;
  return result.user;
}

export function registerWithApi(
  displayName: string,
  email: string,
  password: string,
) {
  return request<ApiUser>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({
      display_name: displayName,
      email,
      password,
    }),
  });
}

export function requestPasswordRecovery(email: string) {
  return request<{ message: string }>("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, newPassword: string) {
  return request<{ message: string }>("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export function clearApiSession() {
  accessToken = null;
}

export async function logoutFromApi() {
  try {
    const response = await fetchApi(
      "/api/v1/auth/logout",
      { method: "POST" },
      null,
    );
    if (!response.ok && response.status !== 401) {
      const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
      const detail = payload?.detail;
      throw new Error(typeof detail === "string" ? detail : `Falha na API (${response.status}).`);
    }
  } finally {
    clearApiSession();
  }
}

export async function verifyEmail(token: string) {
  return request<{ message: string }>("/api/v1/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
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
