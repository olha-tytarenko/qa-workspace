import type { InputHTMLAttributes, ReactNode } from 'react'

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string
  label: string
  error?: string
  /** Extra content rendered between the input and the error message, e.g. a live requirement checklist. */
  hint?: ReactNode
  /** Rendered inside the input, e.g. a password show/hide toggle. */
  trailingAction?: ReactNode
}

export function TextField({
  id,
  label,
  error,
  hint,
  trailingAction,
  ...inputProps
}: TextFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700" htmlFor={id}>
        {label}
        <span className="ml-0.5 text-red-500">*</span>
      </label>
      <div className={trailingAction ? 'relative' : undefined}>
        <input
          id={id}
          className={`w-full rounded-md border bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
            trailingAction ? 'pr-10' : ''
          } ${error ? 'border-red-400' : 'border-gray-300'}`}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          {...inputProps}
        />
        {trailingAction && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">{trailingAction}</div>
        )}
      </div>
      {hint}
      {error && (
        <p className="text-xs text-red-600" id={`${id}-error`}>
          {error}
        </p>
      )}
    </div>
  )
}
