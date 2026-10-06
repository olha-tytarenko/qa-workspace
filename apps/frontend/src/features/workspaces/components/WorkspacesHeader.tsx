import { Brand } from '@/components/Brand.tsx'

export function WorkspacesHeader() {
  return (
    <header className="flex h-12 items-center border-b border-gray-200 bg-white px-6">
      <Brand compact />
    </header>
  )
}
