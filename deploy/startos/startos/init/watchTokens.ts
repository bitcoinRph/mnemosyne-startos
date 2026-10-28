import { addAgentToken } from '../actions/addAgentToken'
import { storeJson } from '../fileModels/store.json'
import { i18n } from '../i18n'
import { sdk } from '../sdk'

export const watchTokens = sdk.setupOnInit(async (effects) => {
  const hasTokens = await storeJson
    .read((s) => Object.keys(s.tokens).length > 0)
    .const(effects)

  if (!hasTokens) {
    await sdk.action.createOwnTask(effects, addAgentToken, 'critical', {
      reason: i18n(
        'Add an agent token so an agent can connect to Mnemosyne. The service starts once one exists.',
      ),
    })
  }
})
