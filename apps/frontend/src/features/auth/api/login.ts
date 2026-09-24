import { useMutation } from '@tanstack/react-query'

import { apiRequest } from '@/lib/api/client.ts'
import type { LoginRequest, LoginResponse } from '@/features/auth/model/types.ts'

function login(payload: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    json: payload,
  })
}

export function useLoginMutation() {
  return useMutation({
    mutationFn: login,
  })
}
