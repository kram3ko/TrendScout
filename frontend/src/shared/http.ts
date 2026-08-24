const API_PREFIX = "/api";
const UNAUTHORIZED = 401;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Raised on 401 so the router can send the user back to the login page. */
export class UnauthorizedError extends ApiError {
  constructor(message: string) {
    super(UNAUTHORIZED, message);
    this.name = "UnauthorizedError";
  }
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return "Some fields are invalid";
  } catch {
    // A non-JSON body (proxy error page, empty 502) carries nothing useful.
  }
  return response.statusText || "Request failed";
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    credentials: "include",
    ...init,
  });

  if (!response.ok) {
    const message = await readError(response);
    throw response.status === UNAUTHORIZED
      ? new UnauthorizedError(message)
      : new ApiError(response.status, message);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export function postJson<T>(path: string, payload: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
