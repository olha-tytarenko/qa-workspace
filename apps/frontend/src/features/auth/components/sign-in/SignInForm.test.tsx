import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, MemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { AppProviders } from '@/app/AppProviders.tsx'
import { createQueryClient } from '@/app/queryClient.ts'
import { server } from '@/test/server.ts'
import { SignInForm } from './SignInForm.tsx'

const LOGIN_URL = 'http://api.test/api/auth/login'
const VALID_PASSWORD = 'a sufficiently long password'
const VALID_EMAIL = 'alice@example.com'

beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://api.test'))
afterEach(() => vi.unstubAllEnvs())

function renderForm() {
  return render(
    <AppProviders queryClient={createQueryClient()}>
      <MemoryRouter>
        <SignInForm />
      </MemoryRouter>
    </AppProviders>,
  )
}

async function fillAndSubmit(email = VALID_EMAIL, password = VALID_PASSWORD) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/^email/i), email)
  await user.type(screen.getByLabelText(/^password/i), password)
  await user.click(screen.getByRole('button', { name: /sign in/i }))
  return user
}

describe('SignInForm', () => {
  test('does not render a Remember me checkbox', () => {
    renderForm()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })

  test('links "Create account" to the sign-up route', () => {
    renderForm()
    expect(screen.getByRole('link', { name: /create account/i })).toHaveAttribute(
      'href',
      '/auth/sign-up',
    )
  })

  test('toggles password visibility', async () => {
    const user = userEvent.setup()
    renderForm()

    const passwordInput = screen.getByLabelText(/^password/i)
    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(screen.getByRole('button', { name: /show password/i }))
    expect(passwordInput).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: /hide password/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('shows required-field errors and does not call the API on an empty submit', async () => {
    let called = false
    server.use(
      http.post(LOGIN_URL, () => {
        called = true
        return HttpResponse.json({ data: {} }, { status: 200 })
      }),
    )
    const user = userEvent.setup()
    renderForm()

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument()
    expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    expect(called).toBe(false)
  })

  test('submits exactly email and password', async () => {
    let requestBody: unknown
    server.use(
      http.post(LOGIN_URL, async ({ request }) => {
        requestBody = await request.json()
        return HttpResponse.json(
          { data: { id: '1', email: VALID_EMAIL, created_at: '2026-01-01T00:00:00Z' } },
          { status: 200 },
        )
      }),
    )

    renderForm()
    await fillAndSubmit()

    expect(requestBody).toEqual({ email: VALID_EMAIL, password: VALID_PASSWORD })
  })

  test('navigates to /workspaces after a successful login', async () => {
    server.use(
      http.post(LOGIN_URL, () =>
        HttpResponse.json(
          { data: { id: '1', email: VALID_EMAIL, created_at: '2026-01-01T00:00:00Z' } },
          { status: 200 },
        ),
      ),
    )

    const router = createMemoryRouter(
      [
        { path: '/auth/sign-in', element: <SignInForm /> },
        { path: '/workspaces', element: <p>Workspaces placeholder</p> },
      ],
      { initialEntries: ['/auth/sign-in'] },
    )
    render(
      <AppProviders queryClient={createQueryClient()}>
        <RouterProvider router={router} />
      </AppProviders>,
    )

    await fillAndSubmit()

    expect(await screen.findByText(/workspaces placeholder/i)).toBeInTheDocument()
  })

  test('shows a generic banner and focuses it on invalid credentials, preserving entered values', async () => {
    server.use(
      http.post(LOGIN_URL, () =>
        HttpResponse.json(
          {
            error: {
              code: 'INVALID_CREDENTIALS',
              message: 'Incorrect email or password.',
              details: {},
              request_id: 'req_1',
            },
          },
          { status: 401 },
        ),
      ),
    )

    renderForm()
    await fillAndSubmit()

    const banner = await screen.findByRole('alert')
    expect(banner).toHaveTextContent(/incorrect email or password/i)
    expect(banner).toHaveFocus()
    expect(screen.getByLabelText(/^email/i)).toHaveValue(VALID_EMAIL)
    expect(screen.getByLabelText(/^password/i)).toHaveValue(VALID_PASSWORD)
    // Never an inline field error — placement must not hint at which field was wrong.
    expect(screen.queryByText(/incorrect/i, { selector: 'p' })).not.toBeInTheDocument()
  })

  test('shows a generic banner on an unexpected server error, without leaking details', async () => {
    server.use(
      http.post(LOGIN_URL, () =>
        HttpResponse.json(
          {
            error: {
              code: 'INTERNAL_ERROR',
              message: 'An unexpected error occurred.',
              details: { trace: 'db/internal/query.py:42' },
              request_id: 'req_2',
            },
          },
          { status: 500 },
        ),
      ),
    )

    renderForm()
    await fillAndSubmit()

    const banner = await screen.findByRole('alert')
    expect(banner).toHaveTextContent(/something went wrong/i)
    expect(banner).toHaveFocus()
    expect(screen.queryByText(/query\.py/)).not.toBeInTheDocument()
  })

  test('shows a generic banner on a network failure', async () => {
    server.use(http.post(LOGIN_URL, () => HttpResponse.error()))

    renderForm()
    await fillAndSubmit()

    const banner = await screen.findByRole('alert')
    expect(banner).toHaveTextContent(/something went wrong/i)
  })
})
