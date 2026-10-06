import { Brand } from '@/components/Brand.tsx'
import { SignOutButton } from '@/features/auth/components/sign-out'

export function WorkspacesHeader() {
  return (
    <header className="flex h-12 items-center justify-between border-b border-gray-200 bg-white px-6">
      <Brand compact />
      <SignOutButton />
    </header>
  )
}
