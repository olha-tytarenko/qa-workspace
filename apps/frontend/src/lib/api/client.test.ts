import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { server } from '../../test/server.ts'
import { ApiError, apiRequest } from './client.ts'

beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://api.test/'))
afterEach(() => vi.unstubAllEnvs())

describe('apiRequest', () => {
  test('calls /api on the configured base URL and always sends cookies', async () => {
    let seen: { credentials: string; accept: string | null } | undefined
    server.use(
      http.get('http://api.test/api/ping', ({ request }) => {
        seen = {
          credentials: request.credentials,
          accept: request.headers.get('Accept'),
        }
        return HttpResponse.json({ pong: true })
      }),
    )

    await expect(apiRequest('/ping')).resolves.toEqual({ pong: true })
    expect(seen).toEqual({ credentials: 'include', accept: 'application/json' })
  })

  test('sends a JSON body with a JSON content type', async () => {
    let received: { body: unknown; contentType: string | null } | undefined
    server.use(
      http.post('http://api.test/api/things', async ({ request }) => {
        received = {
          body: await request.json(),
          contentType: request.headers.get('Content-Type'),
        }
        return HttpResponse.json({ id: '1' }, { status: 201 })
      }),
    )

    await apiRequest('/things', { method: 'POST', json: { name: 'a' } })

    expect(received).toEqual({
      body: { name: 'a' },
      contentType: 'application/json',
    })
  })

  test('turns an error envelope into an ApiError carrying its code', async () => {
    server.use(
      http.get('http://api.test/api/things/1', () =>
        HttpResponse.json(
          {
            error: {
              code: 'NOT_FOUND',
              message: 'No such thing.',
              details: { resource: 'thing' },
              request_id: 'req_123',
            },
          },
          { status: 404 },
        ),
      ),
    )

    const failure = await apiRequest('/things/1').catch((error: unknown) => error)

    expect(failure).toBeInstanceOf(ApiError)
    expect(failure).toMatchObject({
      status: 404,
      code: 'NOT_FOUND',
      message: 'No such thing.',
      details: { resource: 'thing' },
      requestId: 'req_123',
    })
  })

  test('reports a non-envelope failure as UNKNOWN_ERROR instead of success', async () => {
    server.use(
      http.get('http://api.test/api/broken', () =>
        HttpResponse.text('<html>bad gateway</html>', { status: 502 }),
      ),
    )

    await expect(apiRequest('/broken')).rejects.toMatchObject({
      status: 502,
      code: 'UNKNOWN_ERROR',
    })
  })

  test('returns undefined for 204 No Content', async () => {
    server.use(
      http.delete('http://api.test/api/things/1', () => new HttpResponse(null, { status: 204 })),
    )

    await expect(apiRequest('/things/1', { method: 'DELETE' })).resolves.toBeUndefined()
  })

  test('fails clearly when VITE_API_URL is not configured', async () => {
    vi.stubEnv('VITE_API_URL', '')

    await expect(apiRequest('/ping')).rejects.toThrow(/VITE_API_URL/)
  })
})
