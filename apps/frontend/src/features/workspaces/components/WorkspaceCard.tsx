import type { WorkspaceRole } from '@/features/workspaces/model/types.ts'

interface WorkspaceCardProps {
  name: string
  description: string | null
  role: WorkspaceRole
  memberCount: number
  createdAt: string
}

const ROLE_BADGE_STYLES: Record<WorkspaceRole, string> = {
  owner: 'border-indigo-200 bg-indigo-50 text-indigo-700',
  member: 'border-blue-200 bg-blue-50 text-blue-700',
  viewer: 'border-gray-200 bg-gray-100 text-gray-600',
}

const ROLE_LABEL: Record<WorkspaceRole, string> = {
  owner: 'Owner',
  member: 'Member',
  viewer: 'Viewer',
}

// Not clickable: Figma navigates to a per-workspace features screen that
// doesn't exist yet and is out of scope for workspace creation.
export function WorkspaceCard({
  name,
  description,
  role,
  memberCount,
  createdAt,
}: WorkspaceCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-100 text-xs font-bold text-indigo-700">
              {name.charAt(0).toUpperCase()}
            </div>
            <h3 className="text-sm font-semibold text-gray-900">{name}</h3>
          </div>
          {description && <p className="ml-9 text-xs text-gray-500">{description}</p>}
        </div>
        <span
          className={`rounded border px-2 py-0.5 text-xs font-medium ${ROLE_BADGE_STYLES[role]}`}
        >
          {ROLE_LABEL[role]}
        </span>
      </div>
      <div className="ml-9 flex items-center gap-2 text-xs text-gray-400">
        <span>
          {memberCount} {memberCount === 1 ? 'member' : 'members'}
        </span>
        <span>·</span>
        <span>Created {new Date(createdAt).toLocaleDateString()}</span>
      </div>
    </div>
  )
}
