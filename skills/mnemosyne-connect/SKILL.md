---
name: mnemosyne-connect
description: Connect an AI agent to a Mnemosyne memory server that runs on StartOS, and fix connection errors. Use it when the mnemosyne_* tools are missing. Use it when the user says "connect to my Mnemosyne server", "set up Mnemosyne MCP" or "add memory to Claude Code, Codex, Hermes or OpenClaw". Use it when a call fails with 401, 421, a TLS or certificate error, or connection refused. It says where to get the MCP URL and the agent token in StartOS. It gives the setup for each client, explains the StartOS root CA, shows how to test the connection, and has a troubleshooting table.
license: MIT
---

# Connect to Mnemosyne on StartOS

Use this skill to connect an agent to a Mnemosyne server on StartOS. The server has one port. It serves MCP at `/mcp` and a REST API at `/api/v1`.

The client snippets are in `references/clients.md`. After you connect, follow the `mnemosyne-memory` skill.

## What you need

| Item            | Where it comes from                                                     |
| --------------- | ----------------------------------------------------------------------- |
| MCP URL         | The StartOS action **Connection Details** on the Mnemosyne service      |
| REST API URL    | The same action                                                         |
| Agent token     | The StartOS action **Add Agent Token**. StartOS shows it once.          |

You cannot run StartOS actions. Ask the user to run them and to give you the values.

Tell the user:

1. Run **Add Agent Token**. Enter a name for this agent. Use a different name for each agent.
2. Copy the token. No action shows it again.
3. Run **Connection Details**. Copy the **MCP URL**. A list of URLs can appear. Choose an address that this computer can reach.

If the agent runs as a service on the same StartOS server, use the **MCP URL for StartOS services**. It starts with `http://`. It needs no certificate setup.

If the user names an agent that already has a token, **Add Agent Token** replaces that token. The old token stops working.

## Handle the token with care

- Keep the token in the environment variable `MNEMOSYNE_TOKEN`.
- Do not write the token in a file that goes into version control.
- Do not print the token in the chat.
- Use the config forms that read the variable (`${MNEMOSYNE_TOKEN}` or `bearer_token_env_var`).

## Configure the client

Open `references/clients.md`. Use the section for your client:

- Claude Code
- Codex CLI
- Hermes Agent
- OpenClaw
- REST with curl
- Agents that run as StartOS services

Replace `<MCP_URL>` with the real URL. Set `MNEMOSYNE_TOKEN` before you start the client.

## Trust the StartOS root CA

An HTTPS address on the local network uses a certificate from your StartOS server. The client must trust the root CA of the server. Without it, the client shows a TLS or certificate error.

1. Ask the user to download the root CA. Two ways exist. Open `http://<server-name>.local` in a browser (use `http`, not `https`). Or open **About this Server** from the System tab in StartOS.
2. Save the file as `startos-root-ca.pem` on the computer where the agent runs.
3. Set the client option from the table.

| Client      | Option                                                                         |
| ----------- | ------------------------------------------------------------------------------ |
| Claude Code | `NODE_EXTRA_CA_CERTS=/path/to/startos-root-ca.pem`                             |
| Codex CLI   | If the connection fails with a certificate error, set `CODEX_CA_CERTIFICATE=/path/to/startos-root-ca.pem` (or `SSL_CERT_FILE`) |
| Hermes      | `ssl_verify: "~/.hermes/startos-root-ca.pem"` in the server entry              |
| OpenClaw    | If the connection fails with a certificate error, set `NODE_EXTRA_CA_CERTS` for the Gateway process |
| curl        | `--cacert /path/to/startos-root-ca.pem`                                        |

Tor (`.onion`) and public clearnet addresses do not need this step. The StartOS guide "Trusting Your Root CA" explains how to trust the file in an operating system.

Never turn off certificate checks to fix the error.

## Verify the connection

MCP: call the tool `mnemosyne_stats`. A JSON result with `"provider": "mnemosyne"` means success.

REST: run these two commands. Replace `<URL>` with the REST API URL without `/api/v1`:

```bash
curl -sS <URL>/healthz
curl -sS -H "Authorization: Bearer $MNEMOSYNE_TOKEN" <URL>/api/v1/stats
```

The first command returns `{"status":"ok",...}` and needs no token. The second returns the stats of the default bank.

For OpenClaw, also run `openclaw mcp doctor mnemosyne --probe`.

## Troubleshooting

| Symptom                                         | Cause                                                              | Fix                                                                                   |
| ----------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| HTTP 401, "missing bearer token"                | The header is absent or not in the form `Bearer <token>`           | Check the header. Check that `MNEMOSYNE_TOKEN` is set in the process that starts the client. |
| HTTP 401, "invalid bearer token"                | The token is wrong, revoked, or replaced by a newer one            | Ask the user to run **Add Agent Token** for this agent name and to give you the new token. |
| HTTP 421 "Invalid Host header" on `/mcp`        | The URL uses an address that the user has not enabled              | Use an address that **Connection Details** lists. Enabling a new address restarts the service. |
| HTTP 403 on `/mcp`                              | The request has a browser `Origin` header                          | Use a non-browser client                                                              |
| TLS or certificate error                        | The client does not trust the StartOS root CA                      | Trust the root CA (see above)                                                         |
| Connection refused, or timeout                  | The service is stopped, or the address is not reachable            | Ask the user to start the service. Check the network path (LAN, VPN, Tor).            |
| `/healthz` returns 503                          | The server cannot open its database                                | Ask the user to read the service log in StartOS                                       |
| The service does not start, and no token exists | StartOS shows a required step: Add Agent Token                     | Ask the user to run **Add Agent Token**                                               |
| The client connects but lists no tools          | The client used the SSE transport                                  | Set the transport to Streamable HTTP. For OpenClaw, set `transport` to `streamable-http`. |
| The REST call returns 400                       | The body is not a JSON object, an argument is missing, or `author_id` does not match the token name | Fix the body. Do not send `author_id`. |
| HTTP 404 on a REST call                         | The tool name is wrong, or the id does not exist                   | `GET <REST_API_URL>/tools` lists the tool names                                       |

If you cannot fix the error, continue the user's task without memory. Say so once.
