# Mnemosyne

## Documentation

- [Upstream documentation index](https://github.com/mnemosyne-oss/mnemosyne/blob/main/docs/README.md) — the list of all upstream guides
- [Tool reference](https://github.com/mnemosyne-oss/mnemosyne/blob/main/docs/api/tool-schema.mdx) — every memory tool with its parameters
- [Memory hygiene](https://github.com/mnemosyne-oss/mnemosyne/blob/main/docs/hygiene.md) — how to find and remove noisy memories
- [Architecture](https://github.com/mnemosyne-oss/mnemosyne/blob/main/docs/architecture.md) — how working memory, consolidation and search work

## What you get on StartOS

Your agents get a shared long-term memory on your own server. The memory data never leaves your server.

- **MCP URL.** Agents that speak MCP connect here. It ends in `/mcp`.
- **REST API URL.** Scripts and other tools use this. It ends in `/api/v1`.
- **One token for each agent.** Every memory records which agent wrote it.
- **No web page.** You manage the service with three actions. Your agents do the rest.

The service needs no other service and no LLM. It does not consolidate memories on its own. An agent must call the `mnemosyne_sleep` tool.

## Getting set up

The service does not start until you add a token for your first agent.

1. Open the Mnemosyne service.
2. Run **Add Agent Token**.
3. Enter a short name for the agent, for example `hermes`.
4. Copy the token from the result. No action shows it again.
5. Start the service if it is not running.
6. Run **Connection Details** and copy the **MCP URL**.
7. Give the agent the MCP URL and its token (see "Connect an agent").

Make one token for each agent. Use a different name for each agent. The name appears as the author of every memory that the agent writes.

## Connect an agent

Use the **MCP URL** from **Connection Details**. A list of addresses can appear. Choose an address that your agent can reach. The service refuses any address that is not in the list.

Store the token in an environment variable named `MNEMOSYNE_TOKEN`. Do not write the token in a file that you share.

### Claude Code

Run this command:

```bash
claude mcp add --transport http mnemosyne <MCP_URL> --header "Authorization: Bearer <TOKEN>"
```

To keep the token out of a project file, use a `.mcp.json` file:

```json
{
  "mcpServers": {
    "mnemosyne": {
      "type": "http",
      "url": "<MCP_URL>",
      "headers": { "Authorization": "Bearer ${MNEMOSYNE_TOKEN}" }
    }
  }
}
```

### Codex

Run this command:

```bash
codex mcp add mnemosyne --url <MCP_URL> --bearer-token-env-var MNEMOSYNE_TOKEN
```

Or add this to `~/.codex/config.toml`:

```toml
[mcp_servers.mnemosyne]
url = "<MCP_URL>"
bearer_token_env_var = "MNEMOSYNE_TOKEN"
```

### Hermes Agent

Add this to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  mnemosyne:
    url: "<MCP_URL>"
    headers:
      Authorization: "Bearer ${MNEMOSYNE_TOKEN}"
```

Put `MNEMOSYNE_TOKEN=<TOKEN>` in `~/.hermes/.env`. Then run `/reload-mcp` in Hermes.

### OpenClaw

Add this to the OpenClaw configuration. Set `transport` as shown. OpenClaw uses SSE if you omit it, and this service does not serve SSE.

```json
{
  "mcp": {
    "servers": {
      "mnemosyne": {
        "url": "<MCP_URL>",
        "transport": "streamable-http",
        "headers": { "Authorization": "Bearer ${MNEMOSYNE_TOKEN}" }
      }
    }
  }
}
```

To check the connection, run `openclaw mcp doctor mnemosyne --probe`.

### Scripts and other tools (REST)

Use the **REST API URL** from **Connection Details**. Send the token in the `Authorization` header.

```bash
curl -H "Authorization: Bearer $MNEMOSYNE_TOKEN" "<REST_API_URL>/stats"

curl -X POST -H "Authorization: Bearer $MNEMOSYNE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "The user prefers short answers.", "importance": 0.8}' \
  "<REST_API_URL>/memories"
```

The **OpenAPI URL** lists every REST route. It needs no token.

### Agents that run on your server

If the agent is a service on the same StartOS server, use the two URLs for StartOS services from **Connection Details**. They start with `http://`. These URLs need no certificate setup. The agent still needs its own token.

## Trust the StartOS root CA

Some agents run on another computer and use an HTTPS address. Such an agent must trust the root certificate authority (root CA) of your server. Without it, the agent shows a TLS or certificate error.

1. Download the root CA. Open `http://your-server-name.local` in a browser, or open **About this Server** from the System tab in StartOS. Use `http`, not `https`.
2. Save the file on the computer where the agent runs, for example as `startos-root-ca.pem`.
3. Tell the agent to trust the file. Use the setting for your agent in the list below.

| Agent       | Setting                                                                    |
| ----------- | -------------------------------------------------------------------------- |
| Claude Code | Set `NODE_EXTRA_CA_CERTS=/path/to/startos-root-ca.pem`                     |
| Codex       | If you see a certificate error, set `CODEX_CA_CERTIFICATE=/path/to/ca.pem` |
| Hermes      | Add `ssl_verify: "~/.hermes/startos-root-ca.pem"` to the server entry      |
| OpenClaw    | If you see a certificate error, set `NODE_EXTRA_CA_CERTS` for the OpenClaw Gateway process |
| curl        | Add `--cacert /path/to/startos-root-ca.pem`                                |

The StartOS guide "Trusting Your Root CA" explains how to trust the file in your operating system. An address that ends in `.onion` or a public domain does not need this step.

## Install the skills

A skill teaches an agent when to recall, what to remember, and how to keep the memory clean. The `skills` folder of the package repository (`https://github.com/bitcoinRph/mnemosyne-startos`) has three skills:

- `mnemosyne-connect` helps an agent connect and fix connection errors.
- `mnemosyne-memory` is the basic memory protocol. Install this skill first.
- `mnemosyne-second-brain` adds workflows for business notes, clients, decisions and reviews.

Copy the skill folders to the skills folder of your agent:

| Agent             | Folder                                              |
| ----------------- | --------------------------------------------------- |
| Claude Code       | `~/.claude/skills/`                                 |
| Codex             | `~/.agents/skills/`                                 |
| Hermes Agent      | `~/.hermes/skills/`, or `~/.agents/skills/` if you list it in `skills.external_dirs` |
| OpenClaw          | `~/.agents/skills/`                                 |

The `skills/README.md` file in the repository has the exact commands.

## Manage tokens

- **Add Agent Token** makes a token for a new agent. If you use the name of an existing agent, the old token stops working at once.
- **Revoke Agent Token** removes an agent. That agent cannot connect again. Its memories stay.
- **Connection Details** shows the URLs and the agent names. It never shows a token.

Each of these actions restarts the service for a few seconds. If you revoke the last token, the service stops. StartOS then asks you to add a new token.

If a token leaks, run **Add Agent Token** with the same agent name. Then give the agent the new token.

## Banks and privacy

A bank is a separate store of memories. The default bank is `default`. Agents can name other banks, for example `business` or `project-alpha`.

Banks keep memories apart. They do not control access. Every agent that has a valid token can read and write every bank. Give a token only to an agent that you trust with all your memories.

## Backups

A StartOS backup contains all memories and all agent tokens. After a restore, every agent keeps working with its current token. You do not need to do anything.
