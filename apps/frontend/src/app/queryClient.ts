import { QueryClient } from '@tanstack/react-query'

// The single place where server-state defaults are configured. Tests create
// their own client so no cache is shared between them.
export function createQueryClient(): QueryClient {
  return new QueryClient()
}
