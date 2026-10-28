export const DEFAULT_LANG = 'en_US'

const dict = {
  // main.ts
  'MCP and REST API': 0,
  'The memory server is ready': 1,
  'The memory server is not ready': 2,
  // interfaces.ts
  'MCP Endpoint': 3,
  'MCP endpoint (Streamable HTTP) for agents. Authenticate with an agent token as a Bearer token.': 4,
  'REST API': 5,
  'REST API for the same memories. Authenticate with an agent token as a Bearer token.': 6,
  // init/watchTokens.ts
  'Add an agent token so an agent can connect to Mnemosyne. The service starts once one exists.': 7,
  // connection.ts
  'MCP URL': 8,
  'Point MCP clients at this URL.': 9,
  'REST API URL': 10,
  'Base URL of the REST API.': 11,
  'OpenAPI URL': 12,
  'The OpenAPI document for the REST API. It needs no token.': 13,
  'MCP URL for StartOS services': 14,
  'For an agent that runs as a service on this server.': 15,
  'REST API URL for StartOS services': 16,
  // actions/addAgentToken.ts
  'Agent name': 17,
  'A short name for the agent, such as hermes. Memories it writes are attributed to this name.': 18,
  'A short name for the agent, such as hermes. Memories it writes are attributed to this name. Using the name of an existing agent replaces its token and the old token stops working. Existing agents:': 19,
  'Use 1 to 64 lowercase letters, digits, hyphens or underscores, starting with a letter or digit.': 20,
  'Add Agent Token': 21,
  'Create a token for an agent to connect with. Using an existing agent name issues a new token and the old one stops working.': 22,
  'Agent Token': 23,
  'Send the token as an `Authorization: Bearer` header. Copy it now: no action shows it again.': 24,
  Token: 25,
  // actions/revokeAgentToken.ts
  Agent: 26,
  'The agent whose token is revoked.': 27,
  'Revoke Agent Token': 28,
  'Remove an agent token. That agent can no longer connect, and the service restarts. Revoking the last token stops the service until a new one is added.': 29,
  'There are no agent tokens to revoke.': 30,
  'No agent with that name has a token.': 31,
  'Token Revoked': 32,
  'The agent can no longer connect. If this was the last token, the service stays stopped until you add a new one.': 33,
  // actions/connectionDetails.ts
  'Connection Details': 34,
  'Show the URLs agents connect to and the names of the agents that have a token. Tokens are never shown.': 35,
  'Agents authenticate with their own token as an `Authorization: Bearer` header. Use Add Agent Token to create one.': 36,
  Agents: 37,
  'Agents that currently have a token.': 38,
} as const

/**
 * Plumbing. DO NOT EDIT.
 */
export type I18nKey = keyof typeof dict
export type LangDict = Record<(typeof dict)[I18nKey], string>
export default dict
