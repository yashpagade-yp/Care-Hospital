const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ApiError = {
  message: string;
  status: number;
};

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = globalThis.localStorage?.getItem("medcare-session");
  const session = token ? (JSON.parse(token) as { token?: string }) : null;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(session?.token
        ? {
            Authorization: `Bearer ${session.token}`,
          }
        : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Something went wrong. Please try again.";

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Preserve the fallback message when the response is not JSON.
    }

    throw {
      message,
      status: response.status,
    } satisfies ApiError;
  }

  return (await response.json()) as T;
}
