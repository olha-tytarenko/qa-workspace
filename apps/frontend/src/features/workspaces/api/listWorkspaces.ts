import { useQuery } from '@tanstack/react-query'

import { apiRequest } from '@/lib/api/client.ts'
import type { WorkspaceListResponse } from '@/features/workspaces/model/types.ts'
import { workspaceKeys } from './queryKeys.ts'

export function useWorkspacesQuery() {
  return useQuery({
    queryKey: workspaceKeys.list(),
    queryFn: () => apiRequest<WorkspaceListResponse>('/workspaces'),
    // A 401 means "not signed in" — retrying it can't help, and the caller
    // (WorkspacesPage) treats that specific failure as a redirect, not a
    // transient error to recover from.
    retry: false,
  })
}
