import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { AppProviders } from '@/app/AppProviders.tsx'
import { createQueryClient } from '@/app/queryClient.ts'
import { server } from '@/test/server.ts'
import { WorkspacesPage } from './WorkspacesPage.tsx'

const WORKSPACES_URL = 'http://api.test/api/workspaces'

const UNAUTHENTICATED_ERROR = {
  error: {
    code: 'UNAUTHENTICATED',
    message: 'Authentication is required.',
    details: {},
    request_id: 'req_1',
  },
}

function workspace(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: '11111111-1111-1111-1111-111111111111',
    name: 'Acme QA',
    description: 'Core team',
    created_at: '2026-01-01T00:00:00Z',
    role: 'owner',
    member_count: 1,
    ...overrides,
  }
}

beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://api.test'))
afterEach(() => vi.unstubAllEnvs())

function renderPage() {
  const router = createMemoryRouter(
    [
      { path: '/workspaces', element: <WorkspacesPage /> },
      { path: '/auth/sign-in', element: <p>Sign-in placeholder</p> },
    ],
    { initialEntries: ['/workspaces'] },
  )
  render(
    <AppProviders queryClient={createQueryClient()}>
      <RouterProvider router={router} />
    </AppProviders>,
  )
}

describe('WorkspacesPage', () => {
  test('redirects to sign-in when the list request is unauthenticated', async () => {
    server.use(
      http.get(WORKSPACES_URL, () => HttpResponse.json(UNAUTHENTICATED_ERROR, { status: 401 })),
    )

    renderPage()

    expect(await screen.findByText(/sign-in placeholder/i)).toBeInTheDocument()
  })

  test('shows an empty state when the user has no workspaces', async () => {
    server.use(http.get(WORKSPACES_URL, () => HttpResponse.json({ items: [] })))

    renderPage()

    expect(await screen.findByText(/no workspaces yet/i)).toBeInTheDocument()
  })

  test('renders a card for each workspace', async () => {
    server.use(
      http.get(WORKSPACES_URL, () =>
        HttpResponse.json({
          items: [workspace({ name: 'Acme QA' }), workspace({ id: '2', name: 'Mobile Squad' })],
        }),
      ),
    )

    renderPage()

    expect(await screen.findByText('Acme QA')).toBeInTheDocument()
    expect(screen.getByText('Mobile Squad')).toBeInTheDocument()
    expect(screen.getAllByText('Owner')).toHaveLength(2)
  })

  test('creates a workspace and shows it in the list without a page reload', async () => {
    server.use(http.get(WORKSPACES_URL, () => HttpResponse.json({ items: [] })))
    server.use(
      http.post(WORKSPACES_URL, async ({ request }) => {
        const body = (await request.json()) as { name: string; description?: string }
        server.use(
          http.get(WORKSPACES_URL, () =>
            HttpResponse.json({ items: [workspace({ name: body.name })] }),
          ),
        )
        return HttpResponse.json({ data: workspace({ name: body.name }) }, { status: 201 })
      }),
    )

    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: /new workspace/i }))
    await user.type(screen.getByLabelText(/workspace name/i), 'New Team')
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument(),
    )
    expect(await screen.findByText('New Team')).toBeInTheDocument()
  })

  test('does not submit and shows a required error when the name is empty', async () => {
    server.use(http.get(WORKSPACES_URL, () => HttpResponse.json({ items: [] })))
    let called = false
    server.use(
      http.post(WORKSPACES_URL, () => {
        called = true
        return HttpResponse.json({ data: workspace() }, { status: 201 })
      }),
    )

    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: /new workspace/i }))
    await user.click(screen.getByRole('button', { name: /^create workspace$/i }))

    expect(await screen.findByText(/workspace name is required/i)).toBeInTheDocument()
    expect(called).toBe(false)
  })

  test('Escape closes the modal and returns focus to the trigger button', async () => {
    server.use(http.get(WORKSPACES_URL, () => HttpResponse.json({ items: [] })))

    const user = userEvent.setup()
    renderPage()

    const triggerButton = await screen.findByRole('button', { name: /new workspace/i })
    await user.click(triggerButton)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(triggerButton).toHaveFocus()
  })

  test('shows a generic banner in the modal on an unexpected server error, keeping the modal open', async () => {
    server.use(http.get(WORKSPACES_URL, () => HttpResponse.json({ items: [] })))
    server.use(
      http.post(WORKSPACES_URL, () =>
        HttpResponse.json(
          {
            error: {
              code: 'INTERNAL_ERROR',
              message: 'An unexpected error occurred.',
              details: {},
              request_id: 'req_2',
            },
          },
          { status: 500 },
        ),
      ),
    )

    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole('button', { name: /new workspace/i }))
    await user.type(screen.getByLabelText(/workspace name/i), 'Doomed Workspace')
    await user.click(screen.getByRole('button', { name: /^create workspace$/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/something went wrong/i)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByLabelText(/workspace name/i)).toHaveValue('Doomed Workspace')
  })
})
