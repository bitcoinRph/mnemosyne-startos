import { utils } from '@start9labs/start-sdk'
import { connectionMembers, getConnection } from '../connection'
import { storeJson } from '../fileModels/store.json'
import { i18n } from '../i18n'
import { sdk } from '../sdk'
import { agentNameRegex, tokenCharset, tokenLength } from '../utils'

const { InputSpec, Value } = sdk

const inputSpec = InputSpec.of({
  agent: Value.dynamicText(async () => {
    const tokens = (await storeJson.read((s) => s.tokens).once()) ?? {}
    const names = Object.keys(tokens).sort()
    return {
      name: i18n('Agent name'),
      description:
        names.length === 0
          ? i18n(
              'A short name for the agent, such as hermes. Memories it writes are attributed to this name.',
            )
          : `${i18n(
              'A short name for the agent, such as hermes. Memories it writes are attributed to this name. Using the name of an existing agent replaces its token and the old token stops working. Existing agents:',
            )} ${names.join(', ')}`,
      required: true,
      default: null,
      placeholder: 'hermes',
      patterns: [
        {
          regex: agentNameRegex,
          description: i18n(
            'Use 1 to 64 lowercase letters, digits, hyphens or underscores, starting with a letter or digit.',
          ),
        },
      ],
    }
  }),
})

export const addAgentToken = sdk.Action.withInput(
  'add-agent-token',

  {
    name: i18n('Add Agent Token'),
    description: i18n(
      'Create a token for an agent to connect with. Using an existing agent name issues a new token and the old one stops working.',
    ),
    warning: null,
    allowedStatuses: 'any',
    group: null,
    visibility: 'enabled',
  },

  inputSpec,

  async () => null,

  async ({ effects, input }) => {
    const agent = input.agent

    // The form already enforces this; a direct call must not skip it.
    if (!new RegExp(agentNameRegex).test(agent)) {
      throw new Error(
        i18n(
          'Use 1 to 64 lowercase letters, digits, hyphens or underscores, starting with a letter or digit.',
        ),
      )
    }

    const token = utils.getDefaultString({
      charset: tokenCharset,
      len: tokenLength,
    })

    await storeJson.update(effects, (current) => ({
      ...current,
      tokens: { ...current?.tokens, [agent]: token },
    }))

    const connection = await getConnection(effects)

    return {
      version: '1',
      title: i18n('Agent Token'),
      message: i18n(
        'Send the token as an `Authorization: Bearer` header. Copy it now: no action shows it again.',
      ),
      result: {
        type: 'group',
        value: [
          {
            type: 'single',
            name: i18n('Agent name'),
            description: null,
            value: agent,
            masked: false,
            copyable: true,
            qr: false,
            launchable: false,
          },
          {
            type: 'single',
            name: i18n('Token'),
            description: null,
            value: token,
            masked: true,
            copyable: true,
            qr: false,
            launchable: false,
          },
          ...connectionMembers(connection),
        ],
      },
    }
  },
)
