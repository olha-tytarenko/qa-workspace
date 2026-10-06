export function Brand({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-600">
          <span className="text-xs font-bold text-white">QA</span>
        </div>
        <span className="text-sm font-semibold text-gray-800">QA Workspace</span>
      </div>
    )
  }

  return (
    <div className="mb-8 flex justify-center">
      <div className="flex items-center gap-2.5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
          <span className="text-sm font-bold text-white">QA</span>
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900">QA Workspace</p>
          <p className="text-xs text-gray-400">AI-Assisted QA Platform</p>
        </div>
      </div>
    </div>
  )
}
