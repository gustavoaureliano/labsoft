const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

export const apiBaseUrl = (configuredApiUrl || "http://127.0.0.1:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: unknown,
  ) {
    super(`A API respondeu com o status ${status}.`);
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers,
    cache: options.cache ?? "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function teacherHeaders(): Record<string, string> {
  return {
    "X-Teacher-Id": process.env.NEXT_PUBLIC_DEMO_TEACHER_ID
      || "11111111-1111-1111-1111-111111111111",
    "X-Teacher-Name": process.env.NEXT_PUBLIC_DEMO_TEACHER_NAME || "Professor de teste",
  };
}

export function studentHeaders(): Record<string, string> {
  return {
    "X-Student-Id": process.env.NEXT_PUBLIC_DEMO_STUDENT_ID
      || "22222222-2222-2222-2222-222222222222",
  };
}

export function absoluteApiUrl(path: string): string {
  return path.startsWith("http://") || path.startsWith("https://")
    ? path
    : `${apiBaseUrl}${path}`;
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (!(error instanceof ApiError)) return fallback;
  const detail = (error.body as { detail?: string | { message?: string } } | null)?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message || fallback;
}
