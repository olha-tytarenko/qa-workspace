import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { AppProviders } from '@/app/AppProviders.tsx'
import { createQueryClient } from '@/app/queryClient.ts'
import { server } from '@/test/server.ts'
import { SignUpForm } from './SignUpForm.tsx'

const REGISTER_URL = 'http://api.test/api/auth/register'
const VALID_PASSWORD = 'a sufficiently long password'

beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://api.test'))
afterEach(() => vi.unstubAllEnvs())

function renderForm() {
  return render(
    <AppProviders queryClient={createQueryClient()}>
      <MemoryRouter>
        <SignUpForm />
      </MemoryRouter>
    </AppProviders>,
  )
}

function fillForm(password = VALID_PASSWORD, confirmPassword = password) {
  return {
    async run(email = `alice-${Math.random().toString(36).slice(2)}@example.com`) {
      const user = userEvent.setup()
      await user.type(screen.getByLabelText(/work email/i), email)
      await user.type(screen.getByLabelText(/^password/i), password)
      await user.type(screen.getByLabelText(/confirm password/i), confirmPassword)
      await user.click(screen.getByRole('button', { name: /create account/i }))
      return { user, email }
    },
  }
}

describe('SignUpForm', () => {
  test('does not render a Full name field', () => {
    renderForm()
    expect(screen.queryByLabelText(/full name/i)).not.toBeInTheDocument()
  })

  test('links "Already have an account?" to the reserved sign-in route', () => {
    renderForm()
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute(
      'href',
      '/auth/sign-in',
    )
  })

  test('shows required-field errors and does not call the API on an empty submit', async () => {
    let called = false
    server.use(
      http.post(REGISTER_URL, () => {
        called = true
        return HttpResponse.json({ data: {} }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderForm()

    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument()
    expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    expect(screen.getByText(/confirm your password/i)).toBeInTheDocument()
    expect(called).toBe(false)
  })

  test('shows a mismatch error when the passwords differ', async () => {
    renderForm()
    await fillForm(VALID_PASSWORD, 'something else entirely').run()

    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument()
  })

  test('shows a length error for a password under 12 characters', async () => {
    renderForm()
    await fillForm('short', 'short').run()

    expect(await screen.findByText(/password must be at least 12 characters/i)).toBeInTheDocument()
  })

  test('rejects a password whose code-point length is under 12 even when its UTF-16 length is not', async () => {
    // 5 letters + 4 non-BMP emoji: 9 code points (Array.from), but 13 UTF-16
    // units (`.length`) — only code-point counting correctly rejects this,
    // matching the backend's Python `len()` behavior (see tests/test_security.py).
    const password = 'abcde\u{1F600}\u{1F600}\u{1F600}\u{1F600}'
    expect(password.length).toBe(13)
    expect(Array.from(password).length).toBe(9)

    renderForm()
    await fillForm(password, password).run()

    expect(await screen.findByText(/password must be at least 12 characters/i)).toBeInTheDocument()
  })

  test('accepts a password whose code-point length reaches 12 via a non-BMP character', async () => {
    const password = 'abcdefghijk\u{1F600}' // 11 letters + 1 emoji = 12 code points
    expect(Array.from(password).length).toBe(12)

    let requestBody: unknown
    server.use(
      http.post(REGISTER_URL, async ({ request }) => {
        requestBody = await request.json()
        return HttpResponse.json(
          { data: { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' } },
          { status: 201 },
        )
      }),
    )

    renderForm()
    await fillForm(password, password).run()

    await screen.findByRole('heading', { name: /account created/i })
    expect(requestBody).toMatchObject({ password })
  })

  test('submits only email and password, never confirmPassword', async () => {
    let requestBody: unknown
    server.use(
      http.post(REGISTER_URL, async ({ request }) => {
        requestBody = await request.json()
        return HttpResponse.json(
          { data: { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' } },
          { status: 201 },
        )
      }),
    )

    renderForm()
    const { email } = await fillForm().run()

    await screen.findByRole('heading', { name: /account created/i })
    expect(requestBody).toEqual({ email, password: VALID_PASSWORD })
  })

  test('shows the success state without a workspace navigation action', async () => {
    server.use(
      http.post(REGISTER_URL, () =>
        HttpResponse.json(
          { data: { id: '1', email: 'a@example.com', created_at: '2026-01-01T00:00:00Z' } },
          { status: 201 },
        ),
      ),
    )

    renderForm()
    await fillForm().run()

    const heading = await screen.findByRole('heading', { name: /account created/i })
    // The confirmation text is split across elements (the name is in its own
    // `<span>`), so match on the card's combined text content rather than a
    // single text node.
    expect(heading.parentElement).toHaveTextContent('Welcome, there. Your account is ready.')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  test('shows an inline email error and focuses it on a duplicate-email conflict, preserving other values', async () => {
    server.use(
      http.post(REGISTER_URL, () =>
        HttpResponse.json(
          {
            error: {
              code: 'EMAIL_ALREADY_REGISTERED',
              message: 'This email is already registered.',
              details: {},
              request_id: 'req_1',
            },
          },
          { status: 409 },
        ),
      ),
    )

    renderForm()
    await fillForm().run()

    const emailInput = await screen.findByLabelText(/work email/i)
    expect(await screen.findByText(/this email is already registered/i)).toBeInTheDocument()
    expect(emailInput).toHaveFocus()
    expect(screen.getByLabelText(/^password/i)).toHaveValue(VALID_PASSWORD)
    expect(screen.getByLabelText(/confirm password/i)).toHaveValue(VALID_PASSWORD)
  })

  test('shows a generic banner and focuses it on an unexpected server error, without leaking details', async () => {
    server.use(
      http.post(REGISTER_URL, () =>
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
    await fillForm().run()

    const banner = await screen.findByRole('alert')
    expect(banner).toHaveTextContent(/something went wrong/i)
    expect(banner).toHaveFocus()
    expect(screen.queryByText(/query\.py/)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toHaveValue(VALID_PASSWORD)
  })

  test('shows a generic banner on a network failure', async () => {
    server.use(http.post(REGISTER_URL, () => HttpResponse.error()))

    renderForm()
    await fillForm().run()

    const banner = await screen.findByRole('alert')
    expect(banner).toHaveTextContent(/something went wrong/i)
  })
})
