export type WorkspaceRole = 'owner' | 'member' | 'viewer'

export interface Workspace {
  id: string
  name: string
  description: string | null
  created_at: string
  role: WorkspaceRole
  member_count: number
}

export interface WorkspaceCreateRequest {
  name: string
  description?: string
}

export interface WorkspaceResponse {
  data: Workspace
}

export interface WorkspaceListResponse {
  items: Workspace[]
}
