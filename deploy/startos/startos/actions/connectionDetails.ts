import { connectionMembers, getConnection } from '../connection'
import { storeJson } from '../fileModels/store.json'
import { i18n } from '../i18n'
import { sdk } from '../sdk'

export const connectionDetails = sdk.Action.withoutInput(
  'connection-details',

  {
    name: i18n('Connection Details'),
    description: i18n(
      'Show the URLs agents connect to and the names of the agents that have a token. Tokens are never shown.',
    ),
    warning: null,
    allowedStatuses: 'any',
    group: null,
    visibility: 'enabled',
  },

  async ({ effects }) => {
    const tokens = (await storeJson.read((s) => s.tokens).once()) ?? {}
    const agents = Object.keys(tokens).sort()
    const connection = await getConnection(effects)

    return {
      version: '1',
      title: i18n('Connection Details'),
      message: i18n(
        'Agents authenticate with their own token as an `Authorization: Bearer` header. Use Add Agent Token to create one.',
      ),
      result: {
        type: 'group',
        value: [
          ...connectionMembers(connection),
          {
            type: 'multiline',
            name: i18n('Agents'),
            description: i18n('Agents that currently have a token.'),
            value: agents.join('\n'),
            copyable: false,
            qr: false,
            masked: false,
            filename: null,
          },
        ],
      },
    }
  },
)
