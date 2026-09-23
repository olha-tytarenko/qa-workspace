import type { InputHTMLAttributes } from 'react'

import { TextField } from './TextField.tsx'

interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  id: string
  label: string
  error?: string
  /** Whether the live "at least 12 characters" requirement is currently met. */
  lengthMet: boolean
}

export function PasswordField({ lengthMet, ...props }: PasswordFieldProps) {
  return (
    <TextField
      {...props}
      type="password"
      hint={
        <div
          className={`mt-1 flex items-center gap-1.5 text-xs ${
            lengthMet ? 'text-green-600' : 'text-gray-400'
          }`}
        >
          <span aria-hidden="true">{lengthMet ? '✓' : '○'}</span>
          <span>At least 12 characters</span>
        </div>
      }
    />
  )
}
