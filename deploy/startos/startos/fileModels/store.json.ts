import { FileHelper, z } from '@start9labs/start-sdk'
import { sdk } from '../sdk'

// agent name -> bearer token. Lives on the `startos` volume, which no
// subcontainer mounts: the server receives the tokens through its environment.
const shape = z.looseObject({
  tokens: z.record(z.string(), z.string()).catch({}),
})

export const storeJson = FileHelper.json(
  { base: sdk.volumes.startos, subpath: 'store.json' },
  shape,
)
