import { storeJson } from '../fileModels/store.json'
import { sdk } from '../sdk'

export const seedStore = sdk.setupOnInit(async (effects) => {
  const current = await storeJson.read().once()
  if (current === null) {
    await storeJson.write(effects, { tokens: {} })
  }
})
