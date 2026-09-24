import { z } from 'zod'

import { createZodResolver } from '@/lib/forms/zodResolver.ts'

// Backend validation counts Unicode code points (Python `len()`); `.length`
// on a JS string counts UTF-16 code units, which differs for characters
// outside the Basic Multilingual Plane. `Array.from` iterates by code point,
// so the two sides agree on the same password.
function codePointLength(value: string): number {
  return Array.from(value).length
}

export const signUpSchema = z
  .object({
    email: z
      .string()
      .trim()
      .min(1, 'Email is required')
      .email('Enter a valid email address'),
    password: z
      .string()
      .min(1, 'Password is required')
      .refine((value) => codePointLength(value) >= 12, {
        message: 'Password must be at least 12 characters',
      })
      .refine((value) => codePointLength(value) <= 128, {
        message: 'Password must be 128 characters or fewer',
      }),
    confirmPassword: z.string().min(1, 'Confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

export type SignUpFormValues = z.infer<typeof signUpSchema>

export const signUpResolver = createZodResolver(signUpSchema)
