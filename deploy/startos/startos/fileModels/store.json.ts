import { FileHelper } from '@start9labs/start-sdk'
import { sdk } from '../sdk'
import { tokenStoreShape } from './tokenStoreShape'

// agent name -> bearer token. Lives on the `startos` volume, which no
// subcontainer mounts: the server receives the tokens through its environment.
export const storeJson = FileHelper.json(
  { base: sdk.volumes.startos, subpath: 'store.json' },
  tokenStoreShape,
)
