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

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let sessionKnown = false;
let refreshInFlight: Promise<void> | null = null;
const sessionEventKey = "aprovaai-session-event";
// Notification identifier only, not a credential; demo mode also works over LAN HTTP.
const sessionTabId = `${Date.now()}-${Math.random()}`;

export const isApiConfigured = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";

export function hasApiSession() {
  return sessionKnown;
}

function shouldRefresh(path: string) {
  return ![
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
  ].some((endpoint) => path.startsWith(endpoint));
}

async function fetchApi(
  path: string,
  init: RequestInit,
) {
  if (!path.startsWith("/api/") || path.includes("\\")) throw new ApiError("Destino de API inválido.", 400);
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (typeof init.body === "string" && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  return fetch(path, {
    ...init,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
}

async function responseError(response: Response): Promise<ApiError> {
  const payload = await response.json().catch(() => null);
  const detail = payload?.detail;
  return new ApiError(typeof detail === "string" ? detail : typeof detail?.message === "string" ? detail.message : `Falha na API (${response.status}).`, response.status);
}

async function withSessionLock<T>(action: () => Promise<T>): Promise<T> {
  if (typeof navigator === "undefined" || !navigator.locks) {
    throw new ApiError("Este navegador precisa de contexto seguro para coordenar a sessão. Use HTTPS ou localhost.", 503);
  }
  return navigator.locks.request("aprovaai-session", action);
}

export function announceSessionChange(type: "login" | "logout") {
  const message = {type, id: crypto.randomUUID(), sender: sessionTabId};
  try { localStorage.setItem(sessionEventKey, JSON.stringify(message)); } catch { /* BroadcastChannel remains available. */ }
  if (typeof BroadcastChannel !== "undefined") {
    const channel = new BroadcastChannel(sessionEventKey);
    channel.postMessage(message);
    channel.close();
  }
}

export function subscribeSessionChanges(listener: (type: "login" | "logout") => void) {
  let previous = "";
  function receive(message: {type?: string; id?: string; sender?: string} | null) {
    if (!message || message.sender === sessionTabId || !message.id || previous === message.id || !["login", "logout"].includes(message.type ?? "")) return;
    previous = message.id;
    clearApiSession();
    listener(message.type as "login" | "logout");
  }
  const storageListener = (event: StorageEvent) => {
    if (event.key === sessionEventKey && event.newValue) {
      try { receive(JSON.parse(event.newValue)); } catch { /* Ignore invalid notification. */ }
    }
  };
  window.addEventListener("storage", storageListener);
  const channel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel(sessionEventKey) : null;
  if (channel) channel.onmessage = event => receive(event.data);
  return () => { window.removeEventListener("storage", storageListener); channel?.close(); };
}

export async function renewApiSession() {
  if (!refreshInFlight) {
    refreshInFlight = withSessionLock(async () => {
      // Another tab may have renewed the shared cookie while we waited.
      const current = await fetchApi("/api/v1/auth/me", {});
      if (current.ok) { sessionKnown = true; return; }
      if (current.status !== 401) throw await responseError(current);
      const response = await fetchApi("/api/v1/auth/refresh", {method: "POST"});
      if (!response.ok) {
        if (response.status === 401) sessionKnown = false;
        throw await responseError(response);
      }
      // The server updates HttpOnly cookies. Never persist or broadcast tokens.
      sessionKnown = true;
    }).finally(() => { refreshInFlight = null; });
  }
  return refreshInFlight;
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
  allowRefresh = true,
): Promise<T> {
  let response = await fetchApi(path, init);
  const explicitBearer = new Headers(init.headers).has("Authorization");
  const publicVerification = path.startsWith("/api/learning/certificates/verify/");
  if (response.status === 401 && isApiConfigured && allowRefresh && shouldRefresh(path) && !explicitBearer && !publicVerification) {
    const method = (init.method ?? "GET").toUpperCase();
    if (method === "GET" || method === "HEAD") {
      await renewApiSession();
      if (init.signal?.aborted) throw new DOMException("Aborted", "AbortError");
      response = await fetchApi(path, init);
    } else {
      // Do not replay uploads or commands: the user decides whether to retry.
      if (typeof window !== "undefined") window.dispatchEvent(new Event("aprovaai-session-expired"));
      throw new ApiError("Sessão expirada. Renove a sessão e tente novamente; a operação não foi repetida.", 401);
    }
  }
  if (!response.ok) throw await responseError(response);
  if (response.status === 204 || init.method?.toUpperCase() === "HEAD") return undefined as T;
  return response.json() as Promise<T>;
}

export async function loginWithApi(email: string, password: string) {
  return withSessionLock(async () => {
    const result = await request<ApiLogin>("/api/v1/auth/login", {
      method: "POST", body: JSON.stringify({email, password}),
    });
    sessionKnown = true;
    return result.user;
  });
}

export async function getCurrentUserFromApi(allowRefresh = true) {
  const user = await request<ApiUser>("/api/v1/auth/me", {}, allowRefresh);
  sessionKnown = true;
  return user;
}

/*
 * Web requests use the same HttpOnly access cookie as native media requests.
 * Explicit Authorization remains supported for callers that supply it.
 */

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
  sessionKnown = false;
}

export async function logoutFromApi() {
  await withSessionLock(async () => {
    const response = await fetchApi(
      "/api/v1/auth/logout",
      { method: "POST" },
    );
    if (!response.ok && response.status !== 401) {
      throw await responseError(response);
    }
    clearApiSession();
    announceSessionChange("logout");
  });
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
