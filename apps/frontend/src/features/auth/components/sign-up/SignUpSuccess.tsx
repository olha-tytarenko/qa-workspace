export function SignUpSuccess() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-8 py-10 text-center shadow-sm">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
        <svg
          className="h-7 w-7 text-green-600"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h1 className="mb-2 text-xl font-semibold text-gray-900">Account created</h1>
      <p className="mb-7 text-sm text-gray-500">
        Welcome, <span className="font-medium text-gray-700">there</span>. Your account is
        ready.
      </p>
    </div>
  )
}
