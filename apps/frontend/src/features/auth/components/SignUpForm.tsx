import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm, useWatch } from 'react-hook-form'

import { ApiError } from '@/lib/api/client.ts'
import { useRegisterMutation } from '@/features/auth/api/register.ts'
import { signUpResolver, type SignUpFormValues } from '@/features/auth/schemas/signUpSchema.ts'
import { AuthLayout } from './AuthLayout.tsx'
import { ErrorBanner } from './ErrorBanner.tsx'
import { PasswordField } from './PasswordField.tsx'
import { SignUpSuccess } from './SignUpSuccess.tsx'
import { TextField } from './TextField.tsx'

export function SignUpForm() {
  const [succeeded, setSucceeded] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const bannerRef = useRef<HTMLDivElement>(null)
  const registerMutation = useRegisterMutation()

  const {
    register,
    handleSubmit,
    setError,
    setFocus,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SignUpFormValues>({
    resolver: signUpResolver,
    defaultValues: { email: '', password: '', confirmPassword: '' },
  })

  const password = useWatch({ control, name: 'password' })
  const passwordLengthMet = Array.from(password ?? '').length >= 12

  useEffect(() => {
    if (formError) bannerRef.current?.focus()
  }, [formError])

  async function onSubmit(values: SignUpFormValues) {
    setFormError(null)
    try {
      await registerMutation.mutateAsync({ email: values.email, password: values.password })
      setSucceeded(true)
    } catch (error) {
      if (error instanceof ApiError && error.code === 'EMAIL_ALREADY_REGISTERED') {
        setError('email', { type: 'server', message: 'This email is already registered.' })
        setFocus('email')
        return
      }
      setFormError('Something went wrong. Please try again.')
    }
  }

  if (succeeded) {
    return (
      <AuthLayout>
        <SignUpSuccess />
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold text-gray-900">Create account</h1>
        <p className="mb-6 text-sm text-gray-500">
          After creating your account, you can create a workspace or join one through an
          invitation.
        </p>

        {formError && <ErrorBanner message={formError} ref={bannerRef} />}

        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <TextField
            id="email"
            label="Work email"
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />

          <PasswordField
            id="password"
            label="Password"
            placeholder="••••••••"
            autoComplete="new-password"
            error={errors.password?.message}
            lengthMet={passwordLengthMet}
            {...register('password')}
          />

          <TextField
            id="confirmPassword"
            label="Confirm password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />

          <button
            type="submit"
            className="mt-1 inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-indigo-600 bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-gray-500">
          Already have an account?{' '}
          <Link to="/auth/sign-in" className="font-medium text-indigo-600 hover:text-indigo-700">
            Sign in
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}
