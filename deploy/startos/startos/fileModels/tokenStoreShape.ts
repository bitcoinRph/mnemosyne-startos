import { z } from '@start9labs/start-sdk'

const normalizedName = (value: string) => value.trim().toLowerCase()
const normalizedSecret = (value: string) => value.trim()

export const tokenStoreShape = z
  .looseObject({
    tokens: z.record(z.string(), z.string()),
  })
  .superRefine(({ tokens }, context) => {
    const names = new Set<string>()
    const secrets = new Set<string>()

    for (const [name, secret] of Object.entries(tokens)) {
      const cleanName = normalizedName(name)
      const cleanSecret = normalizedSecret(secret)

      if (!cleanName || name !== name.trim()) {
        context.addIssue({
          code: 'custom',
          message: 'Agent names must be non-empty and trimmed',
          path: ['tokens', name],
        })
      } else if (names.has(cleanName)) {
        context.addIssue({
          code: 'custom',
          message: 'Agent names must be unique after normalization',
          path: ['tokens', name],
        })
      }
      names.add(cleanName)

      if (!cleanSecret || secret !== cleanSecret) {
        context.addIssue({
          code: 'custom',
          message: 'Agent secrets must be non-empty and trimmed',
          path: ['tokens', name],
        })
      } else if (secrets.has(cleanSecret)) {
        context.addIssue({
          code: 'custom',
          message: 'Agent secrets must be unique after normalization',
          path: ['tokens', name],
        })
      }
      secrets.add(cleanSecret)
    }
  })
