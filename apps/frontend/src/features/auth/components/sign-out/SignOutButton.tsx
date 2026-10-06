import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { useLogoutMutation } from '@/features/auth/api/logout.ts'

export function SignOutButton() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const logoutMutation = useLogoutMutation()

  function signOut() {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        navigate('/auth/sign-in', { replace: true })
        // Drop every cached server response so the next user who signs in on
        // this tab never sees the previous user's data.
        queryClient.clear()
      },
    })
  }

  return (
    <div className="flex items-center gap-3">
      {logoutMutation.isError && (
        <p role="alert" className="text-sm text-red-600">
          Couldn&apos;t sign out. Please try again.
        </p>
      )}
      <button
        type="button"
        onClick={signOut}
        disabled={logoutMutation.isPending}
        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {logoutMutation.isPending ? 'Signing out…' : 'Sign out'}
      </button>
    </div>
  )
}
