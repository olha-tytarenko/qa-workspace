import { createBrowserRouter, type RouteObject } from 'react-router-dom'
import App from '../App.tsx'

// Route composition lives here. The single route renders the untouched template
// screen until the first product slice adds real routes.
export const routes: RouteObject[] = [{ path: '/', element: <App /> }]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
