import { useQuery } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, expect, test, vi } from 'vitest'
import { apiRequest } from '../lib/api/client.ts'
import { server } from '../test/server.ts'
import { AppProviders } from './AppProviders.tsx'
import { createQueryClient } from './queryClient.ts'
import { routes } from './router.tsx'

afterEach(() => vi.unstubAllEnvs())

function renderStartScreen() {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  render(
    <AppProviders queryClient={createQueryClient()}>
      <RouterProvider router={createMemoryRouter(routes, { initialEntries: ['/'] })} />
    </AppProviders>,
  )
}

test('the start screen shows the workspace list to an authenticated user', async () => {
  server.use(
    http.get('http://api.test/api/workspaces', () =>
      HttpResponse.json({
        items: [
          {
            id: '11111111-1111-1111-1111-111111111111',
            name: 'Acme QA',
            description: null,
            created_at: '2026-01-01T00:00:00Z',
            role: 'owner',
            member_count: 1,
          },
        ],
      }),
    ),
  )

  renderStartScreen()

  expect(await screen.findByRole('heading', { name: 'Workspaces' })).toBeInTheDocument()
  expect(await screen.findByText('Acme QA')).toBeInTheDocument()
})

test('the start screen shows sign-in to an unauthenticated visitor', async () => {
  server.use(
    http.get('http://api.test/api/workspaces', () =>
      HttpResponse.json(
        {
          error: {
            code: 'UNAUTHENTICATED',
            message: 'Authentication is required.',
            details: {},
            request_id: 'req_1',
          },
        },
        { status: 401 },
      ),
    ),
  )

  renderStartScreen()

  expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Workspaces' })).not.toBeInTheDocument()
})

test('providers give components a working query client on top of the API client', async () => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  server.use(http.get('http://api.test/api/ping', () => HttpResponse.json({ pong: true })))

  function Ping() {
    const { data, error } = useQuery({
      queryKey: ['ping'],
      queryFn: () => apiRequest<{ pong: boolean }>('/ping'),
    })
    if (error) return <p>failed</p>
    return <p>{data ? `pong: ${data.pong}` : 'loading'}</p>
  }

  render(
    <AppProviders queryClient={createQueryClient()}>
      <Ping />
    </AppProviders>,
  )

  expect(await screen.findByText('pong: true')).toBeInTheDocument()
})
