import { z } from 'zod'

import { createZodResolver } from '@/lib/forms/zodResolver.ts'

export const createWorkspaceSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Workspace name is required')
    .max(200, 'Workspace name must be 200 characters or fewer'),
  description: z
    .string()
    .trim()
    .max(2000, 'Description must be 2000 characters or fewer')
    .transform((value) => (value.length > 0 ? value : undefined)),
})

export type CreateWorkspaceFormValues = z.infer<typeof createWorkspaceSchema>

export const createWorkspaceResolver = createZodResolver(createWorkspaceSchema)
