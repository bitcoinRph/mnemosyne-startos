import { T } from '@start9labs/start-sdk'
import { i18n } from './i18n'
import { sdk } from './sdk'
import {
  apiHostId,
  apiPort,
  mcpInterfaceId,
  mcpPath,
  openApiPath,
  restInterfaceId,
  restPath,
} from './utils'

export type Connection = {
  mcpUrls: string[]
  restUrls: string[]
  openApiUrls: string[]
  /** For agents that run as StartOS services; null until the binding has a bridge address. */
  bridge: { mcp: string; rest: string; openApi: string } | null
}

/** Reads the addresses the user has enabled, for display in action results. */
export const getConnection = async (
  effects: T.Effects,
): Promise<Connection> => {
  const host = await sdk.host.getOwn(effects, apiHostId).once()
  const binding = host?.bindings[apiPort]

  // Prefer TLS addresses; fall back to whatever is enabled.
  const urlsFor = (interfaceId: string): string[] => {
    const addresses = binding?.interfaces[interfaceId]?.addressInfo.nonLocal
    if (!addresses) return []
    const secure = addresses.filter({ predicate: (h) => h.ssl })
    const chosen = secure.hostnames.length > 0 ? secure : addresses
    return [...new Set(chosen.format())]
  }

  const mcpUrls = urlsFor(mcpInterfaceId)
  const restUrls = urlsFor(restInterfaceId)
  const openApiUrls = [
    ...new Set(restUrls.map((u) => new URL(openApiPath, u).toString())),
  ]

  const bridgeAddress = await sdk.host
    .getBridgeAddress(effects, {
      hostId: apiHostId,
      internalPort: apiPort,
      ssl: false,
    })
    .once()

  return {
    mcpUrls,
    restUrls,
    openApiUrls,
    bridge: bridgeAddress
      ? {
          mcp: `http://${bridgeAddress}${mcpPath}`,
          rest: `http://${bridgeAddress}${restPath}`,
          openApi: `http://${bridgeAddress}${openApiPath}`,
        }
      : null,
  }
}

const urlList = (
  name: string,
  description: string,
  urls: string[],
): T.ActionResultMember[] =>
  urls.length === 0
    ? []
    : [
        {
          type: 'multiline',
          name,
          description,
          value: urls.join('\n'),
          copyable: true,
          qr: false,
          masked: false,
          filename: null,
        },
      ]

const bridgeUrl = (
  name: string,
  description: string,
  url: string | undefined,
): T.ActionResultMember[] =>
  url === undefined
    ? []
    : [
        {
          type: 'single',
          name,
          description,
          value: url,
          copyable: true,
          qr: false,
          masked: false,
          launchable: false,
        },
      ]

/** Result members that list where agents can connect. Never includes a token. */
export const connectionMembers = (conn: Connection): T.ActionResultMember[] => [
  ...urlList(
    i18n('MCP URL'),
    i18n('Point MCP clients at this URL.'),
    conn.mcpUrls,
  ),
  ...urlList(
    i18n('REST API URL'),
    i18n('Base URL of the REST API.'),
    conn.restUrls,
  ),
  ...urlList(
    i18n('OpenAPI URL'),
    i18n('The OpenAPI document for the REST API. It needs no token.'),
    conn.openApiUrls,
  ),
  ...bridgeUrl(
    i18n('MCP URL for StartOS services'),
    i18n('For an agent that runs as a service on this server.'),
    conn.bridge?.mcp,
  ),
  ...bridgeUrl(
    i18n('REST API URL for StartOS services'),
    i18n('For an agent that runs as a service on this server.'),
    conn.bridge?.rest,
  ),
]
