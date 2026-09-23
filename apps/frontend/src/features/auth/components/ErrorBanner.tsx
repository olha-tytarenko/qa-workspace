import { forwardRef } from 'react'

export const ErrorBanner = forwardRef<HTMLDivElement, { message: string }>(function ErrorBanner(
  { message },
  ref,
) {
  return (
    <div
      className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"
      role="alert"
      tabIndex={-1}
      ref={ref}
    >
      {message}
    </div>
  )
})
