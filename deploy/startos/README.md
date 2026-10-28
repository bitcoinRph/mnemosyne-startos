<p align="center">
  <img src="icon.webp" alt="Mnemosyne Logo" width="21%">
</p>

# Mnemosyne on StartOS

> Everything not listed in this document should behave the same as upstream
> Mnemosyne. If a feature, setting, or behavior is not mentioned here, the
> upstream documentation is accurate and fully applicable. See the
> Documentation section of `instructions.md` for links.

Mnemosyne is a local-first memory server for AI agents. It stores memories in SQLite, searches them with vectors and full text, and serves the same 30 tools over MCP and a REST API. This package runs it on one port, with one Bearer token per agent. Upstream: <https://github.com/mnemosyne-oss/mnemosyne>.

---

## Table of Contents

- [Image and Container Runtime](#image-and-container-runtime)
- [Volume and Data Layout](#volume-and-data-layout)
- [File Models](#file-models)
- [Dependencies](#dependencies)
- [Network Access and Interfaces](#network-access-and-interfaces)
- [Installation and First-Run Flow](#installation-and-first-run-flow)
- [Actions](#actions)
- [Tasks](#tasks)
- [Health Checks](#health-checks)
- [Backups and Restore](#backups-and-restore)
- [Limitations and Differences](#limitations-and-differences)
- [Quick Reference for AI Consumers](#quick-reference-for-ai-consumers)

---

## Image and Container Runtime

The package builds one image from a fork of upstream Mnemosyne. The fork lives in the same repository, and the package is in `deploy/startos/`. The build context is the repository root, and the Dockerfile is `deploy/startos/Dockerfile`.

| What                | Value                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------ |
| Image source        | Custom Dockerfile. It installs the fork from source at the commit that the package pins.   |
| Python extras       | `mcp`, `embeddings`, `sync`, `media`                                                       |
| StartOS server      | The `mnemosyne-startos` Python package from `deploy/startos/server/`, installed beside the fork |
| Embedding model     | `BAAI/bge-small-en-v1.5`, downloaded at image build time into `/opt/mnemosyne/fastembed`  |
| Runtime network     | Offline. `HF_HUB_OFFLINE=1` is set, so the model is never fetched at runtime.              |
| Architectures       | x86_64, aarch64                                                                            |
| Entrypoint          | `mnemosyne-startos-server --host 0.0.0.0 --port 8080`. StartOS passes the same command.    |
| Subcontainers       | One: `mnemosyne-sub`. It runs the single daemon `primary`.                                 |

`mnemosyne-startos-server` is one ASGI process on one port. It serves `/healthz`, `/openapi.json`, the REST API under `/api/v1`, and the MCP endpoint at `/mcp`. It does not use the upstream `mnemosyne mcp` command. It imports private helpers from `mnemosyne.mcp_server` (the Bearer middleware, the Streamable HTTP app builder, and the token parser) so MCP behaves exactly as upstream. The REST routes call the same tool handler as MCP, so both surfaces have the same behavior and the same 30 tools.

The server refuses to start (exit code 2) when `MNEMOSYNE_MCP_TOKENS` is empty or unset, and when it cannot open the default bank.

Environment variables baked into the image: `MNEMOSYNE_DATA_DIR`, `MNEMOSYNE_HOME`, `HERMES_HOME`, `MNEMOSYNE_SHARED_DB_PATH`, `MNEMOSYNE_BACKUP_DIR`, `MNEMOSYNE_BLOB_DIR`, `MNEMOSYNE_FASTEMBED_CACHE_DIR`, `HF_HUB_OFFLINE`. The package sets no LLM, no media model, and no `MNEMOSYNE_MCP_BANK`. The default scope for new memories is `global`. The default bank is `default`.

To open a shell in the running service:

```bash
start-cli package attach mnemosyne -n mnemosyne-sub -- <cmd>
```

## Volume and Data Layout

The package has two volumes. Only `main` is mounted in the subcontainer. The `startos` volume holds the token store and no subcontainer can read it.

| Volume    | Mount point          | Content                                                                                       |
| --------- | -------------------- | --------------------------------------------------------------------------------------------- |
| `main`    | `/data` (read-write) | All memory data (see below)                                                                   |
| `startos` | none                 | `store.json`, the agent token store. The server gets tokens through its environment instead.  |

Paths on `main`:

| Path                                | Content                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------- |
| `/data/mnemosyne/mnemosyne.db`      | SQLite database of the `default` bank                                        |
| `/data/mnemosyne/banks/<name>/`     | One SQLite database per named bank                                           |
| `/data/mnemosyne/shared/mnemosyne.db` | The shared surface store (the `mnemosyne_shared_*` tools)                  |
| `/data/mnemosyne/blobs`             | Media blobs for `mnemosyne_remember_media`                                   |
| `/data/home`                        | Mnemosyne home. `/data/home/hermes` is the Hermes home that upstream reads.  |
| `/data/backups`                     | Upstream backup directory. Tool calls such as `mnemosyne_export` can write here. |

The database is embedded SQLite. No external database exists.

## File Models

The package owns one file model: `store.json` on the `startos` volume. It holds the agent tokens. Nothing else is written as a configuration file.

| File                       | Format | Seeded                                  | Rewritten by                                | Hand edit                          |
| -------------------------- | ------ | --------------------------------------- | ------------------------------------------- | ---------------------------------- |
| `startos` volume `store.json` | JSON, shape `{ "tokens": { "<agent>": "<secret>" } }` | At install, with `tokens` set to `{}` | The `add-agent-token` and `revoke-agent-token` actions | Survives, and a changed token list restarts the service. Not supported. |

Settings that reach the application through environment variables are set again on every start:

- `MNEMOSYNE_MCP_TOKENS` is a JSON object built from `store.json`. The server reads it once at launch, so a change in the token list restarts the service.
- `MNEMOSYNE_MCP_ALLOWED_HOSTS` is a comma-separated list of Host header values. The package computes it from every address that the user enables on the `api` host, plus the StartOS bridge IP, `127.0.0.1` and `localhost`. It lists each name twice: the bare name and `name:*`. Enabling or disabling an address changes the list and restarts the service. A user cannot set it by hand.

Upstream `config.yaml` is not written. Environment overrides that upstream supports cannot be set from the StartOS UI.

## Dependencies

None.

## Network Access and Interfaces

The service exposes one port, 8080, with plain HTTP. StartOS terminates TLS in front of it. The host id is `api`. Two interfaces share the binding and differ only by path.

| Interface id | Type | Port | Protocol | Path       | Purpose                                                                  |
| ------------ | ---- | ---- | -------- | ---------- | ------------------------------------------------------------------------ |
| `mcp`        | api  | 8080 | http     | `/mcp`     | MCP over Streamable HTTP. Bearer auth. Host header allowlist.            |
| `rest`       | api  | 8080 | http     | `/api/v1`  | REST API over the same tools. Bearer auth. No Host header check.         |

Two more routes exist on the same port and have no interface of their own. Both need no token and no Host match.

| Route           | Purpose                                                                       |
| --------------- | ----------------------------------------------------------------------------- |
| `/healthz`      | `200 {"status":"ok","version":...}`, or a redacted `503 {"status":"unavailable"}` |
| `/openapi.json` | OpenAPI document for the REST API                                             |

REST routes. All of them need `Authorization: Bearer <agent token>`. The body of a call is the JSON arguments of the tool.

| Method and path                   | Tool called            | Notes                                              |
| --------------------------------- | ---------------------- | -------------------------------------------------- |
| `GET /api/v1/tools`               | none                   | Lists the tool definitions                         |
| `POST /api/v1/tools/{name}`       | any tool by name       | The only route for tools without a shortcut        |
| `POST /api/v1/memories`           | `mnemosyne_remember`   |                                                    |
| `POST /api/v1/recall`             | `mnemosyne_recall`     |                                                    |
| `GET /api/v1/memories/{id}`       | `mnemosyne_get`        | `?bank=` selects the bank                          |
| `PATCH /api/v1/memories/{id}`     | `mnemosyne_update`     | The path id wins over a `memory_id` in the body    |
| `DELETE /api/v1/memories/{id}`    | `mnemosyne_forget`     | `?bank=` selects the bank                          |
| `GET /api/v1/stats`               | `mnemosyne_stats`      | `?bank=` selects the bank                          |
| `POST /api/v1/batch`              | `mnemosyne_batch`      |                                                    |

Status codes of the REST API:

| Code | Meaning                                                                                              |
| ---- | ---------------------------------------------------------------------------------------------------- |
| 200  | The tool ran. Read `status` in the body for a tool-level result such as `filtered`.                  |
| 400  | Body is not a JSON object, a required argument is missing, a batch fails validation, or `author_id` differs from the token name |
| 401  | Missing, malformed or unknown Bearer token. The response has `WWW-Authenticate: Bearer`.             |
| 404  | Unknown tool name, or the tool returned `not_found`                                                  |
| 500  | The tool failed or returned a `status` of `error`                                                    |

On `/mcp`, a Host header that is not in the allowlist gets `421 Invalid Host header`. A browser `Origin` header gets `403`, because the origin allowlist is empty. CLI and SDK clients send no `Origin` and are not affected. The MCP endpoint is Streamable HTTP only. The legacy SSE transport is not served.

## Installation and First-Run Flow

The package generates no credential at install. It starts no service until the user creates a first agent token.

1. At install, the package seeds `store.json` with an empty token list.
2. A critical task asks for the `add-agent-token` action. The service stays stopped while that task exists.
3. After the user adds a token, the service starts and the health check goes green once `/healthz` returns 200.

The first start of each bank creates its database. The `default` bank database is created at startup so `/healthz` is green before any client connects. Named banks are created on first use.

There is no setup wizard, no admin account and no web UI.

## Actions

The package has three user-facing actions. None is hidden. All three run in any service status.

**`add-agent-token`**

- When to run it: for each new agent, and to rotate the token of an existing agent.
- What it changes: writes a new random secret for the agent name in `store.json` on the `startos` volume. The secret has 48 characters from `a-z`, `A-Z` and `0-9`. A name that already exists gets a new secret, and the old secret stops working at once.
- Cost: a service restart of a few seconds. It cuts open MCP sessions and REST calls. No memory data changes.
- Repeat safety: safe. Each run with the same name issues a new secret and replaces the previous one.
- Outputs: the agent name, the secret (shown once, masked, copyable), and the URL list from `connection-details`. No action shows the secret again.
- The agent name becomes the author of every memory that the agent writes. A later rename is not possible. Revoke and add a new name instead, and the old memories keep the old author.

**`revoke-agent-token`**

- When to run it: when an agent is retired or a token leaks.
- What it changes: removes the agent from `store.json`. Memories that the agent wrote stay, with the old author.
- Cost: a service restart of a few seconds.
- Repeat safety: a second run for the same name fails with an error, because the name is gone. The action is disabled while no tokens exist.
- What happens next: if it removed the last token, the service stops and the critical task returns (see Tasks).

**`connection-details`**

- When to run it: when a user or an agent needs the URLs, or needs to know which agent names exist.
- What it changes: nothing.
- Outputs: the MCP URL, the REST API URL and the OpenAPI URL for each enabled address. TLS addresses are preferred, and any enabled address is used if none has TLS. It also shows the two plain-HTTP bridge URLs for agents that run as StartOS services, and the list of agent names. It never shows a secret. A missing URL means that the address is not enabled.

## Tasks

The package creates one task. It is the only reason the service stays stopped without a visible error.

| Task              | Severity   | What raises it                                         | What clears it                                        | Where it appears       |
| ----------------- | ---------- | ------------------------------------------------------ | ----------------------------------------------------- | ---------------------- |
| `add-agent-token` | `critical` | The token list in `store.json` is empty                | Running `add-agent-token` once, so the list has one entry | The Mnemosyne service page |

The task can return. An init watcher reads the token list reactively, so revoking the last token raises it again and the service stops. While the task exists, StartOS blocks the start of the service, and the user sees the task instead of the usual controls. If the service starts anyway with no tokens, `main.ts` throws and the server also refuses to start.

## Health Checks

The package has one check, `primary`, shown as "MCP and REST API". It probes `GET http://127.0.0.1:8080/healthz` with a 3 second timeout. The grace period is 60 seconds.

| Result                                | Meaning                                                                                       |
| ------------------------------------- | --------------------------------------------------------------------------------------------- |
| success, "The memory server is ready" | `/healthz` returned 200, so the default bank database opens                                   |
| failure inside the grace period       | The process is still starting. Wait. It is the normal state for the first seconds.            |
| failure after the grace period        | The server is not listening, or `/healthz` returned 503                                       |

The check requires a 2xx response from `/healthz`. A 503 is a fault, not a slow start. The public response is deliberately generic; the service log records the underlying exception. The usual cause is a SQLite error on the default bank database, such as a full disk, a wrong permission on `/data/mnemosyne`, or a corrupt file.

A server that exits at once with code 2 prints the reason on stderr. The usual reason is an empty `MNEMOSYNE_MCP_TOKENS`.

Diagnosis of client errors:

| Symptom                                      | Cause and fix                                                                                          |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `401` on `/mcp` or `/api/v1`                 | The token is missing, malformed, revoked, or replaced by a newer one for the same agent name. Run `add-agent-token` and give the agent the new secret. |
| `421 Invalid Host header` on `/mcp`          | The client used an address that the user has not enabled. Run `connection-details` and use a listed URL. Enabling an address restarts the service and adds it to the allowlist. |
| `403` on `/mcp`                              | The request carried a browser `Origin` header. Use a non-browser client.                              |
| `503` on `/healthz`                          | The default bank database cannot open (see above)                                                      |
| Connection refused                           | The service is stopped, or the critical task is open                                                   |
| TLS error on an HTTPS address                | The client does not trust the StartOS root CA. This is a client setting. The service sees no request. |

## Backups and Restore

The strategy is a wholesale copy of both volumes with `Backups.ofVolumes('main', 'startos')`. No database dump runs, so the SQLite files are copied as files.

- Included: every bank database, the shared surface store, media blobs, `/data/home`, `/data/backups`, and `store.json` with all agent tokens.
- MCP and REST file imports/exports accept only a flat filename directly beneath `/data/backups`; directories, traversal, absolute paths, links, and non-regular files are rejected.
- Excluded: the image and the embedding model. They come from the package, not from a volume.
- After restore: nothing is required. Tokens come back with `store.json`, so every agent keeps its current secret and URL settings. If the restored server has other enabled addresses, an agent that uses a disabled address gets `421`. Enable the address again to fix it.

## Limitations and Differences

1. The package has no web UI. Users work through MCP, REST, and the three actions.
2. Consolidation does not run on its own. It runs only when a client calls `mnemosyne_sleep`. It needs no LLM.
3. The package does not run a sync relay. The `sync_push`, `sync_pull` and `sync_status` tools, the persona tools and `mnemosyne_triple_end` are not served, because upstream does not expose them over MCP.
4. The SSE transport is not served. Clients must use Streamable HTTP.
5. The package configures no LLM and no media model. Calls that need one, such as `extract=true` on `mnemosyne_remember` and media understanding in `mnemosyne_remember_media`, return no extracted data or the status `unavailable`.
6. Banks separate data and are not access control. Any valid token can read and write every bank, the shared surface store and the canonical profile. Canonical facts use one owner, `default`, for the whole server.
7. A token is a full-access credential for one agent name. The package has no read-only token and no per-bank token.
8. Author attribution is enforced. The author of a memory is the token name. A call that sets a different `author_id` gets `400`.
9. `mnemosyne_export` and file-based `mnemosyne_import` accept only a flat filename directly beneath `/data/backups`. `mnemosyne_remember_media` with a local path reads inside the subcontainer and also needs `MNEMOSYNE_MEDIA_ALLOWED_PATHS`, which the package does not set. Provider imports (`hindsight`, `mem0`) need outbound network and an API key.
10. The file import reads only the JSON that `mnemosyne_export` writes.
11. Changing the token list or the enabled addresses restarts the service.
12. Upstream is a beta release line. Behavior can change between versions, and the REST routes are specific to this package, not to upstream.
13. The server imports private helpers from `mnemosyne.mcp_server`, so an upstream refactor can break the package build until the wrapper is updated.

---

## Quick Reference for AI Consumers

```yaml
package_id: mnemosyne
image: mnemosyne # built from deploy/startos/Dockerfile, context is the repo root
architectures: [x86_64, aarch64]
subcontainers: [mnemosyne-sub]
volumes:
  main: /data
  startos: null # not mounted, holds store.json
file_models:
  - store.json # startos volume
startos_managed_env_vars:
  - MNEMOSYNE_MCP_TOKENS
  - MNEMOSYNE_MCP_ALLOWED_HOSTS
dependencies: none
interfaces:
  mcp: { type: api, port: 8080 } # path /mcp
  rest: { type: api, port: 8080 } # path /api/v1
actions:
  - add-agent-token
  - revoke-agent-token
  - connection-details
tasks:
  - { action: add-agent-token, severity: critical }
health_checks:
  - primary
```
