import type { Workspace } from '@/features/workspaces/model/types.ts'
import { WorkspaceCard } from './WorkspaceCard.tsx'

export function WorkspaceList({ workspaces }: { workspaces: Workspace[] }) {
  if (workspaces.length === 0) {
    return (
      <div className="flex flex-col items-center rounded-lg border border-dashed border-gray-300 py-16 text-center">
        <h3 className="mb-1 text-sm font-semibold text-gray-700">No workspaces yet</h3>
        <p className="max-w-sm text-sm text-gray-500">
          Create a workspace to start tracking product specifications and QA coverage.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {workspaces.map((workspace) => (
        <WorkspaceCard
          key={workspace.id}
          name={workspace.name}
          description={workspace.description}
          role={workspace.role}
          memberCount={workspace.member_count}
          createdAt={workspace.created_at}
        />
      ))}
    </div>
  )
}
