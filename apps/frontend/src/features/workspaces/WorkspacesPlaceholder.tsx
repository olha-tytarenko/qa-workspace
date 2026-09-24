// Deliberately empty: no workspace data model, API, or fetching exist yet.
// This is only the landing point after a successful login.
export function WorkspacesPlaceholder() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7] px-4">
      <p className="text-sm text-gray-500">Workspaces</p>
    </div>
  )
}
