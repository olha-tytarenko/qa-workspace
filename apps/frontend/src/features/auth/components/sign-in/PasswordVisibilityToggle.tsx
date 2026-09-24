export function PasswordVisibilityToggle({
  visible,
  onToggle,
}: {
  visible: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="cursor-pointer text-xs text-gray-400 hover:text-gray-600"
      aria-label={visible ? 'Hide password' : 'Show password'}
    >
      {visible ? 'Hide' : 'Show'}
    </button>
  )
}
