// Minimal API client convention. Every backend call goes through `apiRequest`:
//   - the base URL comes from `VITE_API_URL`, and paths are relative to `/api`;
//   - cookies are always sent (`credentials: 'include'`) for session auth;
//   - non-2xx responses become an `ApiError` built from the API error envelope
//     `{ "error": { "code", "message", "details", "request_id" } }`.
// Callers branch on `ApiError.code`, never on `message`.

export interface ApiErrorBody {
  code: string
  message: string
  details?: Record<string, unknown>
  request_id?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown> | undefined
  readonly requestId: string | undefined

  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code
    this.details = body.details
    this.requestId = body.request_id
  }
}

export type ApiRequestInit = Omit<RequestInit, 'body' | 'credentials'> & {
  /** Sent as a JSON body. */
  json?: unknown
}

function getApiBaseUrl(): string {
  // Read on use, not at import time, so importing this module never throws.
  const baseUrl = import.meta.env.VITE_API_URL
  if (!baseUrl) {
    throw new Error('VITE_API_URL is not set. See apps/frontend/.env.example.')
  }
  return baseUrl.replace(/\/+$/, '')
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as Record<string, unknown>
  return typeof candidate.code === 'string' && typeof candidate.message === 'string'
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const payload: unknown = await response.json()
    const body =
      typeof payload === 'object' && payload !== null
        ? (payload as { error?: unknown }).error
        : undefined
    if (isErrorBody(body)) return new ApiError(response.status, body)
  } catch {
    // Not JSON: fall through to the generic error below.
  }
  return new ApiError(response.status, {
    code: 'UNKNOWN_ERROR',
    message: response.statusText || 'The request failed.',
  })
}

/**
 * `path` starts with `/` and is relative to `/api`, e.g. `apiRequest('/workspaces')`
 * (a future product endpoint). The unprefixed `/health` probe is not reachable
 * through this client.
 * The response body is returned as `T` without runtime validation; validate it
 * at the call site once real endpoints and schemas exist.
 */
export async function apiRequest<T>(
  path: string,
  { json, headers, ...init }: ApiRequestInit = {},
): Promise<T> {
  const requestHeaders = new Headers(headers)
  requestHeaders.set('Accept', 'application/json')
  if (json !== undefined) requestHeaders.set('Content-Type', 'application/json')

  const response = await fetch(`${getApiBaseUrl()}/api${path}`, {
    ...init,
    headers: requestHeaders,
    body: json === undefined ? undefined : JSON.stringify(json),
    credentials: 'include',
  })

  if (!response.ok) throw await toApiError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
