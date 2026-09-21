import { useQuery } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, expect, test, vi } from 'vitest'
import { apiRequest } from '../lib/api/client.ts'
import { server } from '../test/server.ts'
import { AppProviders } from './AppProviders.tsx'
import { createQueryClient } from './queryClient.ts'
import { routes } from './router.tsx'

afterEach(() => vi.unstubAllEnvs())

test('the composed application renders its root route and responds to input', async () => {
  const user = userEvent.setup()
  render(
    <AppProviders queryClient={createQueryClient()}>
      <RouterProvider router={createMemoryRouter(routes)} />
    </AppProviders>,
  )

  expect(screen.getByRole('heading', { name: 'Get started' })).toBeInTheDocument()

  const counter = screen.getByRole('button', { name: /count is 0/i })
  await user.click(counter)
  expect(counter).toHaveTextContent('Count is 1')
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
