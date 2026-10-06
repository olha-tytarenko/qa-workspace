import { useEffect, type RefObject } from 'react'
import { useForm } from 'react-hook-form'

import { ErrorBanner } from '@/components/ErrorBanner.tsx'
import { TextField } from '@/components/TextField.tsx'
import { useCreateWorkspaceMutation } from '@/features/workspaces/api/createWorkspace.ts'
import {
  createWorkspaceResolver,
  type CreateWorkspaceFormValues,
} from '@/features/workspaces/schemas/createWorkspaceSchema.ts'
import { TextareaField } from './TextareaField.tsx'

export function CreateWorkspaceModal({
  onClose,
  triggerRef,
}: {
  onClose: () => void
  triggerRef: RefObject<HTMLButtonElement | null>
}) {
  const createWorkspaceMutation = useCreateWorkspaceMutation()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateWorkspaceFormValues>({
    resolver: createWorkspaceResolver,
    defaultValues: { name: '', description: '' },
  })

  useEffect(() => {
    document.getElementById('workspace-name')?.focus()
  }, [])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') close()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `close` is stable enough for this one-time listener; re-adding it on every render would be wasteful
  }, [])

  function close() {
    onClose()
    triggerRef.current?.focus()
  }

  async function onSubmit(values: CreateWorkspaceFormValues) {
    try {
      await createWorkspaceMutation.mutateAsync(values)
      close()
    } catch {
      // Rendered declaratively below via createWorkspaceMutation.isError —
      // nothing call-site-specific to do here, unlike the auth forms.
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={close} />
      <div
        className="relative mx-4 w-full max-w-md rounded-xl border border-gray-200 bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-workspace-title"
      >
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 id="create-workspace-title" className="text-base font-semibold text-gray-900">
            Create workspace
          </h2>
          <button
            type="button"
            onClick={close}
            className="cursor-pointer text-xl leading-none text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form
          className="flex flex-col gap-4 px-6 py-5"
          onSubmit={handleSubmit(onSubmit)}
          noValidate
        >
          {createWorkspaceMutation.isError && (
            <ErrorBanner message="Something went wrong. Please try again." />
          )}

          <p className="rounded border border-indigo-100 bg-indigo-50 p-3 text-xs text-gray-500">
            You will become the Owner of this workspace and can invite team members once
            it's created.
          </p>

          <TextField
            id="workspace-name"
            label="Workspace name"
            placeholder="e.g. Acme Product Team"
            error={errors.name?.message}
            {...register('name')}
          />

          <TextareaField
            id="workspace-description"
            label="Description (optional)"
            placeholder="What does this workspace cover?"
            rows={3}
            error={errors.description?.message}
            {...register('description')}
          />

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={close}
              className="rounded-md border border-gray-300 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md border border-indigo-600 bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? 'Creating…' : 'Create workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
