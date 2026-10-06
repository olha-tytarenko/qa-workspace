import { useRef, useState } from 'react'
import { Navigate } from 'react-router-dom'

import { ApiError } from '@/lib/api/client.ts'
import { useWorkspacesQuery } from '@/features/workspaces/api/listWorkspaces.ts'
import { CreateWorkspaceModal } from './CreateWorkspaceModal.tsx'
import { WorkspaceList } from './WorkspaceList.tsx'
import { WorkspacesHeader } from './WorkspacesHeader.tsx'

export function WorkspacesPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const newWorkspaceButtonRef = useRef<HTMLButtonElement>(null)
  const workspacesQuery = useWorkspacesQuery()

  if (
    workspacesQuery.isError &&
    workspacesQuery.error instanceof ApiError &&
    workspacesQuery.error.code === 'UNAUTHENTICATED'
  ) {
    return <Navigate to="/auth/sign-in" replace />
  }

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <WorkspacesHeader />

      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Workspaces</h1>
            <p className="mt-1 text-sm text-gray-500">
              Your product specification and QA workspaces.
            </p>
          </div>
          <button
            ref={newWorkspaceButtonRef}
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="rounded-md border border-indigo-600 bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            + New workspace
          </button>
        </div>

        {workspacesQuery.isPending ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : workspacesQuery.isSuccess ? (
          <WorkspaceList workspaces={workspacesQuery.data.items} />
        ) : (
          <p className="text-sm text-red-600">Something went wrong. Please try again.</p>
        )}
      </div>

      {showCreateModal && (
        <CreateWorkspaceModal
          onClose={() => setShowCreateModal(false)}
          triggerRef={newWorkspaceButtonRef}
        />
      )}
    </div>
  )
}
