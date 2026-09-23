import type { ReactNode } from 'react'

import { Brand } from './Brand.tsx'

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#f5f5f7] px-4">
      <div className="w-full max-w-sm">
        <Brand />
        {children}
      </div>
    </div>
  )
}
