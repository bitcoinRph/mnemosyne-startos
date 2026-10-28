import { storeJson } from '../fileModels/store.json'
import { i18n } from '../i18n'
import { sdk } from '../sdk'

const { InputSpec, Value } = sdk

const inputSpec = InputSpec.of({
  agent: Value.dynamicSelect(async () => {
    const tokens = (await storeJson.read((s) => s.tokens).once()) ?? {}
    return {
      name: i18n('Agent'),
      description: i18n('The agent whose token is revoked.'),
      default: null,
      values: Object.fromEntries(
        Object.keys(tokens)
          .sort()
          .map((n) => [n, n]),
      ),
    }
  }),
})

export const revokeAgentToken = sdk.Action.withInput(
  'revoke-agent-token',

  async ({ effects }) => {
    const hasTokens = await storeJson
      .read((s) => Object.keys(s.tokens).length > 0)
      .const(effects)

    return {
      name: i18n('Revoke Agent Token'),
      description: i18n(
        'Remove an agent token. That agent can no longer connect, and the service restarts. Revoking the last token stops the service until a new one is added.',
      ),
      warning: null,
      allowedStatuses: 'any',
      group: null,
      visibility: hasTokens
        ? 'enabled'
        : { disabled: i18n('There are no agent tokens to revoke.') },
    }
  },

  inputSpec,

  async () => null,

  async ({ effects, input }) => {
    const agent = input.agent
    const tokens = await storeJson.read((s) => s.tokens).once()
    if (!tokens || !Object.keys(tokens).includes(agent)) {
      throw new Error(i18n('No agent with that name has a token.'))
    }

    // merge() cannot drop one entry of a record, so rebuild the whole value.
    await storeJson.update(effects, (current) => ({
      ...current,
      tokens: Object.fromEntries(
        Object.entries(current?.tokens ?? {}).filter(
          ([name]) => name !== agent,
        ),
      ),
    }))

    return {
      version: '1',
      title: i18n('Token Revoked'),
      message: i18n(
        'The agent can no longer connect. If this was the last token, the service stays stopped until you add a new one.',
      ),
      result: null,
    }
  },
)
