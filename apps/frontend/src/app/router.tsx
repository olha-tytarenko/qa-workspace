import { createBrowserRouter, Navigate, type RouteObject } from 'react-router-dom'

import { SignInForm } from '@/features/auth/components/sign-in'
import { SignUpForm } from '@/features/auth/components/sign-up'
import { WorkspacesPage } from '@/features/workspaces/components'

// Route composition lives here.
export const routes: RouteObject[] = [
  // The start screen. /workspaces sends an unauthenticated visitor to
  // sign-in on its own 401, so no separate auth check is needed here.
  { path: '/', element: <Navigate to="/workspaces" replace /> },
  { path: '/auth/sign-up', element: <SignUpForm /> },
  { path: '/auth/sign-in', element: <SignInForm /> },
  { path: '/workspaces', element: <WorkspacesPage /> },
]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
