import { createBrowserRouter, type RouteObject } from 'react-router-dom'

import App from '@/App.tsx'
import { SignUpForm } from '@/features/auth/components/SignUpForm.tsx'

// Route composition lives here.
export const routes: RouteObject[] = [
  { path: '/', element: <App /> },
  { path: '/auth/sign-up', element: <SignUpForm /> },
]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
