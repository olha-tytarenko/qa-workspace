import { useMutation } from '@tanstack/react-query'

import { apiRequest } from '@/lib/api/client.ts'

function logout(): Promise<void> {
  return apiRequest<void>('/auth/logout', { method: 'POST' })
}

export function useLogoutMutation() {
  return useMutation({
    mutationFn: logout,
  })
}
