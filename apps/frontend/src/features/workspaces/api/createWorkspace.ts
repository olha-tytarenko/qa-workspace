import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiRequest } from '@/lib/api/client.ts'
import type {
  WorkspaceCreateRequest,
  WorkspaceResponse,
} from '@/features/workspaces/model/types.ts'
import { workspaceKeys } from './queryKeys.ts'

function createWorkspace(payload: WorkspaceCreateRequest): Promise<WorkspaceResponse> {
  return apiRequest<WorkspaceResponse>('/workspaces', {
    method: 'POST',
    json: payload,
  })
}

export function useCreateWorkspaceMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createWorkspace,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.list() })
    },
  })
}
