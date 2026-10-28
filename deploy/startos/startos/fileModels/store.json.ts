import { FileHelper } from '@start9labs/start-sdk'
import { sdk } from '../sdk'
import {
  parseTokenStoreJson,
  type TokenStore,
  tokenStoreShape,
} from './tokenStoreShape'

// agent name -> bearer token. Lives on the `startos` volume, which no
// subcontainer mounts: the server receives the tokens through its environment.
export const storeJson = FileHelper.raw<TokenStore>(
  { base: sdk.volumes.startos, subpath: 'store.json' },
  (value) => JSON.stringify(value, null, 2),
  parseTokenStoreJson,
  (value) => tokenStoreShape.parse(value),
)
