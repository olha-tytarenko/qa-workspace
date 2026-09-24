import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'

import { ApiError } from '@/lib/api/client.ts'
import { useLoginMutation } from '@/features/auth/api/login.ts'
import { signInResolver, type SignInFormValues } from '@/features/auth/schemas/signInSchema.ts'
import { AuthLayout, ErrorBanner, TextField } from '@/features/auth/components/common'
import { PasswordVisibilityToggle } from './PasswordVisibilityToggle.tsx'

export function SignInForm() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const bannerRef = useRef<HTMLDivElement>(null)
  const loginMutation = useLoginMutation()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignInFormValues>({
    resolver: signInResolver,
    defaultValues: { email: '', password: '' },
  })

  useEffect(() => {
    if (formError) bannerRef.current?.focus()
  }, [formError])

  async function onSubmit(values: SignInFormValues) {
    setFormError(null)
    try {
      await loginMutation.mutateAsync(values)
      navigate('/workspaces')
    } catch (error) {
      if (error instanceof ApiError && error.code === 'INVALID_CREDENTIALS') {
        setFormError('Incorrect email or password.')
      } else {
        setFormError('Something went wrong. Please try again.')
      }
    }
  }

  return (
    <AuthLayout>
      <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold text-gray-900">Welcome back</h1>
        <p className="mb-6 text-sm text-gray-500">Sign in to your account</p>

        {formError && <ErrorBanner message={formError} ref={bannerRef} />}

        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <TextField
            id="email"
            label="Email"
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />

          <TextField
            id="password"
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            autoComplete="current-password"
            error={errors.password?.message}
            trailingAction={
              <PasswordVisibilityToggle
                visible={showPassword}
                onToggle={() => setShowPassword((value) => !value)}
              />
            }
            {...register('password')}
          />

          <div className="flex justify-end">
            <button type="button" className="text-xs text-indigo-600 hover:text-indigo-700">
              Forgot password?
            </button>
          </div>

          <button
            type="submit"
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-indigo-600 bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-gray-500">
          Don't have an account?{' '}
          <Link to="/auth/sign-up" className="font-medium text-indigo-600 hover:text-indigo-700">
            Create account
          </Link>
        </p>
      </div>

      <p className="mt-6 text-center text-xs text-gray-400">AI proposes. Humans decide.</p>
    </AuthLayout>
  )
}
