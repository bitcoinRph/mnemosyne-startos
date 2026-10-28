import { utils } from '@start9labs/start-sdk'
import { storeJson } from './fileModels/store.json'
import { i18n } from './i18n'
import { sdk } from './sdk'
import { apiHostId, apiPort, healthPath } from './utils'

export const main = sdk.setupMain(async ({ effects }) => {
  const tokens = await storeJson.read((s) => s.tokens).const(effects)
  if (!tokens || Object.keys(tokens).length === 0) {
    // The critical task from init/watchTokens.ts keeps the service stopped
    // until a token exists, so reaching this means that task was bypassed.
    throw new Error('No agent tokens exist; run the Add Agent Token action')
  }

  // Hostnames a client can put in the Host header, taken from the binding so
  // they follow the addresses the user enables. Mapped to plain strings so the
  // service restarts only when this set changes.
  const addressNames = await sdk.host
    .getOwn(effects, apiHostId, (host) => {
      if (!host) return []
      const names = utils
        .filledAddress(host, {
          hostId: apiHostId,
          internalPort: apiPort,
          username: null,
          scheme: null,
          sslScheme: null,
          suffix: '',
        })
        .hostnames.map((h) =>
          h.metadata.kind === 'ipv6' ? `[${h.hostname}]` : h.hostname,
        )
      return [...new Set(names)].sort()
    })
    .const()

  // Other StartOS services reach this one at the bridge address
  // (<osIp>:<assigned port>), and a local client may use the loopback names.
  const osIp = await sdk.getOsIp(effects)
  const names = [
    ...new Set([...addressNames, osIp, '127.0.0.1', 'localhost']),
  ].sort()

  // A client on a default port (80 or 443) sends the Host header without a
  // port, which `name:*` does not match, so each name is allowed both ways.
  const allowedHosts = names.flatMap((name) => [name, `${name}:*`])

  return sdk.Daemons.of(effects).addDaemon('primary', {
    subcontainer: sdk.SubContainer.of(
      effects,
      { imageId: 'mnemosyne' },
      sdk.Mounts.of().mountVolume({
        volumeId: 'main',
        subpath: null,
        mountpoint: '/data',
        readonly: false,
      }),
      'mnemosyne-sub',
    ),
    exec: {
      command: sdk.useEntrypoint([
        'mnemosyne-startos-server',
        '--host',
        '0.0.0.0',
        '--port',
        String(apiPort),
      ]),
      env: {
        MNEMOSYNE_MCP_TOKENS: JSON.stringify(tokens),
        MNEMOSYNE_MCP_ALLOWED_HOSTS: allowedHosts.join(','),
        MNEMOSYNE_BACKUP_DIR: '/data/backups',
      },
    },
    ready: {
      display: i18n('MCP and REST API'),
      // checkWebUrl succeeds on any HTTP response, including the 503 that
      // /healthz returns while the memory database cannot be opened.
      fn: async () => {
        try {
          const res = await fetch(`http://127.0.0.1:${apiPort}${healthPath}`, {
            signal: AbortSignal.timeout(3_000),
          })
          if (res.ok) {
            return {
              result: 'success',
              message: i18n('The memory server is ready'),
            }
          }
        } catch {
          // Not listening yet: reported below as a failure, which the grace
          // period shows as starting. Logging here would repeat every second.
        }
        return {
          result: 'failure',
          message: i18n('The memory server is not ready'),
        }
      },
      gracePeriod: 60_000,
    },
    requires: [],
  })
})
