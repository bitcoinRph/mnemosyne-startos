export const apiPort = 8080
export const apiHostId = 'api'
export const mcpInterfaceId = 'mcp'
export const restInterfaceId = 'rest'
export const mcpPath = '/mcp'
export const restPath = '/api/v1'
export const openApiPath = '/openapi.json'
export const healthPath = '/healthz'

// Must stay in step with the agent-name rule enforced by the server.
export const agentNameRegex = '^[a-z0-9][a-z0-9_-]{0,63}$'

export const tokenCharset = 'a-z,A-Z,0-9'
export const tokenLength = 48
