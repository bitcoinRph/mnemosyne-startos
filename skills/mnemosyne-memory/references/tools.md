# Mnemosyne tool reference

This server exposes 30 tools over MCP and REST. Every tool name starts with `mnemosyne_`. Parameters in **bold** are required. Every tool that has a `bank` parameter uses the bank `default` when you omit it.

REST: `POST <REST_API_URL>/tools/<tool name>` with the arguments as a JSON body. These shortcuts also exist:

| Shortcut                           | Tool                 |
| ---------------------------------- | -------------------- |
| `POST /memories`                   | `mnemosyne_remember` |
| `POST /recall`                     | `mnemosyne_recall`   |
| `GET /memories/{id}?bank=`         | `mnemosyne_get`      |
| `PATCH /memories/{id}`             | `mnemosyne_update`   |
| `DELETE /memories/{id}?bank=`      | `mnemosyne_forget`   |
| `GET /stats?bank=`                 | `mnemosyne_stats`    |
| `POST /batch`                      | `mnemosyne_batch`    |

Do not send `author_id`. The server sets it from your token name.

## Write and change memories

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_remember` | **content**, importance (0 to 1, default 0.5), source, scope (`global` default or `session`), valid_until (`YYYY-MM-DD`), veracity, metadata, extract_entities, bank | You learn a durable fact. Returns `memory_id`. Status `filtered` means the server refused it. |
| `mnemosyne_update` | **memory_id**, content, importance, bank | A stored fact needs a small fix |
| `mnemosyne_invalidate` | **memory_id**, replacement_id, bank | A fact is no longer true. Keeps history. |
| `mnemosyne_validate` | **memory_id**, **action** (`attest`, `update`, `invalidate`, `delete`), validator, new_content (with `update`), note, store (`private` or `surface`), bank | You record that a fact is confirmed or corrected, with a reason |
| `mnemosyne_forget` | **memory_id**, bank | The user wants a memory deleted |
| `mnemosyne_batch` | **operations** (50 at most), dry_run, bank | You write several memories at once, atomically |
| `mnemosyne_remember_media` | **ref**, modality, mime, title, hint, max_moments, importance, scope, bank | You register an image, audio, video or document by URL. This server has no media model, so the status is often `unavailable`. |

`mnemosyne_batch` operation fields: **action** (`remember`, `update`, `forget`, `invalidate`), content, memory_id, importance, source, scope, valid_until, metadata, veracity, replacement_id.

Do not use `extract` on this server. It needs an LLM, and none is configured.

## Read memories

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_recall` | **query**, limit (default 5), temporal_weight (0 to 0.5), temporal_halflife (hours), query_time, explain, bank | You look for memories on a topic. Each result has an `id`. |
| `mnemosyne_get` | **memory_id**, bank | You need the full record of one memory |
| `mnemosyne_stats` | bank | You check the store, or you test the connection |

## Profile (canonical facts)

The profile has one owner for the whole server. All agents share it.

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_remember_canonical` | **category**, **name**, **body**, source, confidence, bank | You set a stable profile value. A new value replaces the old one. |
| `mnemosyne_recall_canonical` | category, name, query, include_history, limit, bank | You read one value, list a category or search the profile |
| `mnemosyne_forget_canonical` | **category**, **name**, bank | You retire a profile value |

## Relationships and time

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_triple_add` | **subject**, **predicate**, **object**, valid_from (`YYYY-MM-DD`), source, confidence, bank | You record a relationship or a dated fact |
| `mnemosyne_triple_query` | subject, predicate, object, as_of (`YYYY-MM-DD`), bank | You ask what was true, now or on a date |
| `mnemosyne_graph_link` | **source_id**, **target_id**, **relationship**, weight (0 to 1), bank | You link two memories, for example `caused` or `supersedes` |
| `mnemosyne_graph_query` | **seed_memory_id**, max_hops (default 2), edge_type, min_weight, bank | You walk the links from one memory |

Triple notes for this server:

- `mnemosyne_triple_add` always closes the open triple with the same subject and predicate. It ignores `valid_until` and `supersede`.
- The predicates `mentions`, `fact`, `occurred_on` and `has_source` go to a separate annotation table.
- `mnemosyne_triple_end` exists in the schema file but this server does not expose it.

## Working notes

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_scratchpad_write` | **content**, bank | You save a temporary note |
| `mnemosyne_scratchpad_read` | bank | You read the temporary notes |
| `mnemosyne_scratchpad_clear` | bank | The task ends |

## Shared surface

The shared surface is a small store of cross-agent facts. It is separate from banks. Use it only when the user asks for a fact that all agents must see.

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_shared_remember` | **content**, kind (`meta`, `preference`, `correction`, `identity`), importance (default 0.8), veracity, metadata | You write a shared fact |
| `mnemosyne_shared_recall` | **query**, limit | You read shared facts |
| `mnemosyne_shared_forget` | **memory_id** | You remove a shared fact |
| `mnemosyne_shared_stats` | none | You check the shared store |

Do not start `content` with `[USER]` or `[ASSISTANT]`. The server rejects raw conversation text.

## Maintenance

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_sleep` | all_sessions, dry_run, force, bank | You consolidate working memories. Run it on a schedule. |
| `mnemosyne_hygiene_audit` | limit (default 200), offset, scan_all, batch_size, min_score (default 0.3), tables, bank | You look for noisy or secret-bearing rows. It only reads. |
| `mnemosyne_hygiene_clean` | **candidates_json**, action (`delete`, `archive`, `flag`, `keep`), confirm, bank | You act on audit candidates. It is a dry run until `confirm` is true. |
| `mnemosyne_diagnose` | repair_vec_working, dry_run, bank | You check or repair the vector index |

## Export and import

These tools read and write files inside the server container. An agent cannot read those files over MCP or REST.

| Tool | Key parameters | Use when |
| ---- | -------------- | -------- |
| `mnemosyne_export` | **output_path**, bank | The user wants a JSON export. Use a path under `/data/backups/`. |
| `mnemosyne_import` | input_path, provider (`hindsight` or `mem0`), api_key, user_id, agent_id, base_url, dry_run, force, channel_id, bank | You restore a Mnemosyne export, or you copy from another provider. Always try `dry_run` first. |

The file import accepts only JSON that `mnemosyne_export` wrote. To load plain notes, write them with `mnemosyne_batch`.
