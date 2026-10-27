import { i18n } from './i18n'
import { sdk } from './sdk'
import {
  apiHostId,
  apiPort,
  mcpInterfaceId,
  mcpPath,
  restInterfaceId,
  restPath,
} from './utils'

export const setInterfaces = sdk.setupInterfaces(async ({ effects }) => {
  const apiMulti = sdk.MultiHost.of(effects, apiHostId)
  const apiOrigin = await apiMulti.bindPort(apiPort, { protocol: 'http' })

  const mcp = sdk.createInterface(effects, {
    name: i18n('MCP Endpoint'),
    id: mcpInterfaceId,
    description: i18n(
      'MCP endpoint (Streamable HTTP) for agents. Authenticate with an agent token as a Bearer token.',
    ),
    type: 'api',
    masked: false,
    schemeOverride: null,
    username: null,
    path: mcpPath,
    query: {},
  })

  const rest = sdk.createInterface(effects, {
    name: i18n('REST API'),
    id: restInterfaceId,
    description: i18n(
      'REST API for the same memories. Authenticate with an agent token as a Bearer token.',
    ),
    type: 'api',
    masked: false,
    schemeOverride: null,
    username: null,
    path: restPath,
    query: {},
  })

  return [await apiOrigin.export([mcp, rest])]
})
