import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { AppProviders } from '@/app/AppProviders.tsx'
import { createQueryClient } from '@/app/queryClient.ts'
import { server } from '@/test/server.ts'
import { SignOutButton } from './SignOutButton.tsx'

const LOGOUT_URL = 'http://api.test/api/auth/logout'

beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://api.test'))
afterEach(() => vi.unstubAllEnvs())

function renderSignedInScreen() {
  const queryClient = createQueryClient()
  // Stands in for data a signed-in user has already loaded.
  queryClient.setQueryData(['workspaces'], { items: [{ name: 'Private Workspace' }] })
  const router = createMemoryRouter(
    [
      { path: '/workspaces', element: <SignOutButton /> },
      { path: '/auth/sign-in', element: <p>Sign-in placeholder</p> },
    ],
    { initialEntries: ['/workspaces'] },
  )
  render(
    <AppProviders queryClient={queryClient}>
      <RouterProvider router={router} />
    </AppProviders>,
  )
  return { queryClient, router }
}

describe('SignOutButton', () => {
  test('signs out, goes to sign-in, and forgets cached server data', async () => {
    let logoutCalls = 0
    server.use(
      http.post(LOGOUT_URL, () => {
        logoutCalls += 1
        return new HttpResponse(null, { status: 204 })
      }),
    )

    const user = userEvent.setup()
    const { queryClient } = renderSignedInScreen()

    await user.click(screen.getByRole('button', { name: /sign out/i }))

    expect(await screen.findByText(/sign-in placeholder/i)).toBeInTheDocument()
    expect(logoutCalls).toBe(1)
    expect(queryClient.getQueryData(['workspaces'])).toBeUndefined()
  })

  test('stays signed in and shows an error when sign-out fails', async () => {
    server.use(
      http.post(LOGOUT_URL, () =>
        HttpResponse.json(
          {
            error: {
              code: 'INTERNAL_ERROR',
              message: 'An unexpected error occurred.',
              details: {},
              request_id: 'req_1',
            },
          },
          { status: 500 },
        ),
      ),
    )

    const user = userEvent.setup()
    const { queryClient, router } = renderSignedInScreen()

    await user.click(screen.getByRole('button', { name: /sign out/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn.t sign out/i)
    expect(router.state.location.pathname).toBe('/workspaces')
    expect(screen.getByRole('button', { name: /sign out/i })).toBeEnabled()
    expect(queryClient.getQueryData(['workspaces'])).toBeDefined()
  })
})
