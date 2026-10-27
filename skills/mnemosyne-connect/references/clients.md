# Client setup for Mnemosyne on StartOS

Replace `<MCP_URL>` with the **MCP URL** from the StartOS action **Connection Details**. Set `MNEMOSYNE_TOKEN` to the token from **Add Agent Token** before you start the client. If your computer does not trust the HTTPS address yet, also set the root CA option for the client (see the table at the end).

## Claude Code

Add the server with a command. Choose a scope with `--scope local`, `--scope project` or `--scope user`.

```bash
claude mcp add --transport http mnemosyne <MCP_URL> --header "Authorization: Bearer <TOKEN>"
```

To read the token from the environment, put this in `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "mnemosyne": {
      "type": "http",
      "url": "<MCP_URL>",
      "headers": {
        "Authorization": "Bearer ${MNEMOSYNE_TOKEN}"
      }
    }
  }
}
```

`${VAR}` expansion works in this file. Do not name the variable `ANTHROPIC_*`.

Skills folders: `~/.claude/skills/<name>/SKILL.md` (user) and `.claude/skills/<name>/SKILL.md` (project).

## Codex CLI

Add the server with a command:

```bash
codex mcp add mnemosyne --url <MCP_URL> --bearer-token-env-var MNEMOSYNE_TOKEN
```

Or edit `~/.codex/config.toml`:

```toml
[mcp_servers.mnemosyne]
url = "<MCP_URL>"
bearer_token_env_var = "MNEMOSYNE_TOKEN"
```

Skills folders: `~/.codex/skills` or `~/.agents/skills` (user), `.agents/skills` (repository).

## Hermes Agent

Edit `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  mnemosyne:
    url: "<MCP_URL>"
    headers:
      Authorization: "Bearer ${MNEMOSYNE_TOKEN}"
    ssl_verify: "~/.hermes/startos-root-ca.pem"
```

Remove the `ssl_verify` line if the address does not need the root CA. Hermes reads `${MNEMOSYNE_TOKEN}` from `~/.hermes/.env` first, then from the process environment. Run `/reload-mcp` after each change.

Skills folders: `~/.hermes/skills/`, an extra folder in `skills.external_dirs` (for example `~/.agents/skills`), or `.hermes/skills` and `.agents/skills` in a project. Run `hermes skills trust` once to trust a project folder.

## OpenClaw

Add this to the OpenClaw configuration. Always set `transport`. OpenClaw uses SSE when you omit it, and this server does not serve SSE.

```json
{
  "mcp": {
    "servers": {
      "mnemosyne": {
        "url": "<MCP_URL>",
        "transport": "streamable-http",
        "headers": {
          "Authorization": "Bearer ${MNEMOSYNE_TOKEN}"
        }
      }
    }
  }
}
```

Or use the command line. This command sets no token, so add the `headers` block from the configuration above:

```bash
openclaw mcp add mnemosyne --url <MCP_URL> --transport streamable-http
openclaw mcp doctor mnemosyne --probe
```

Skills folders: `<workspace>/skills`, `<workspace>/.agents/skills`, `~/.agents/skills` and `~/.openclaw/skills`.

## REST with curl

Use the **REST API URL** from **Connection Details**. It ends in `/api/v1`.

```bash
export REST_URL="<REST_API_URL>"

# Store a memory
curl -sS -X POST "$REST_URL/memories" \
  -H "Authorization: Bearer $MNEMOSYNE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "The user prefers short answers.", "importance": 0.8, "veracity": "stated"}'

# Recall
curl -sS -X POST "$REST_URL/recall" \
  -H "Authorization: Bearer $MNEMOSYNE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "answer length preference", "limit": 5}'

# Any other tool, by name
curl -sS -X POST "$REST_URL/tools/mnemosyne_stats" \
  -H "Authorization: Bearer $MNEMOSYNE_TOKEN"
```

`GET <REST_API_URL>/tools` lists the tools. The OpenAPI document is at `/openapi.json` on the same host and needs no token.

## Agents that run as StartOS services

An agent that runs as a service on the same StartOS server uses the plain HTTP bridge URLs from **Connection Details**:

- **MCP URL for StartOS services**, for example `http://10.0.3.1:<port>/mcp`
- **REST API URL for StartOS services**

These URLs need no root CA. The agent still needs its own token. Put the token in the secret or environment setting of that service. Use the config forms of the client sections above.

## Root CA options

| Client      | Option                                                                         |
| ----------- | ------------------------------------------------------------------------------ |
| Claude Code | `NODE_EXTRA_CA_CERTS=/path/to/startos-root-ca.pem`. You can put it in the `env` block of `~/.claude/settings.json`. |
| Codex CLI   | If the connection fails with a certificate error, set `CODEX_CA_CERTIFICATE=/path/to/ca.pem` or `SSL_CERT_FILE` |
| Hermes      | `ssl_verify` in the server entry                                               |
| OpenClaw    | If the connection fails with a certificate error, set `NODE_EXTRA_CA_CERTS` for the Gateway process |
| curl        | `--cacert /path/to/startos-root-ca.pem`                                        |
