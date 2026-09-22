import { z } from 'zod'
import type { Resolver } from 'react-hook-form'

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

// No `@hookform/resolvers` dependency is installed (out of this slice's
// approved scope), so this adapts `signUpSchema` to react-hook-form's
// `Resolver` shape directly: one first issue per field path, matching how
// react-hook-form surfaces a single message per field.
export const signUpResolver: Resolver<SignUpFormValues> = (values) => {
  const result = signUpSchema.safeParse(values)
  if (result.success) return { values: result.data, errors: {} }

  const errors: Record<string, { type: string; message: string }> = {}
  for (const issue of result.error.issues) {
    const path = issue.path.join('.')
    if (!errors[path]) errors[path] = { type: issue.code, message: issue.message }
  }
  return { values: {}, errors }
}
