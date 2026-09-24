import { createBrowserRouter, type RouteObject } from 'react-router-dom'

import App from '@/App.tsx'
import { SignInForm } from '@/features/auth/components/sign-in'
import { SignUpForm } from '@/features/auth/components/sign-up'
import { WorkspacesPlaceholder } from '@/features/workspaces/WorkspacesPlaceholder.tsx'

// Route composition lives here.
export const routes: RouteObject[] = [
  { path: '/', element: <App /> },
  { path: '/auth/sign-up', element: <SignUpForm /> },
  { path: '/auth/sign-in', element: <SignInForm /> },
  { path: '/workspaces', element: <WorkspacesPlaceholder /> },
]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
