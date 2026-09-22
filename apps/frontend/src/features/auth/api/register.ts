import { useMutation } from '@tanstack/react-query'

import { apiRequest } from '@/lib/api/client.ts'
import type { RegisterRequest, RegisterResponse } from '@/features/auth/model/types.ts'

function register(payload: RegisterRequest): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>('/auth/register', {
    method: 'POST',
    json: payload,
  })
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: register,
  })
}
