---
name: mnemosyne-memory
description: Operating protocol for an AI agent that uses Mnemosyne long-term memory over MCP or REST. Use it when mnemosyne_* tools are available. Use it when the user says "remember", "recall", "don't forget", "what do we know about", "long-term memory" or "my memory server". It says when to recall before you answer. It says what to store and what to skip. It covers writing one clear fact per memory, updating instead of duplicating, banks, canonical facts, triples, the scratchpad, maintenance (sleep, hygiene) and server failures. If the tools are missing, use the mnemosyne-connect skill first.
license: MIT
---

# Mnemosyne memory protocol

Mnemosyne is a long-term memory server. It keeps facts between sessions and between agents. Use it so the user does not repeat things.

This skill covers the basic protocol. The file `references/tools.md` lists every tool with its parameters. For business workflows, use the `mnemosyne-second-brain` skill.

## How you reach the tools

- MCP: call the tools by name, for example `mnemosyne_recall`.
- REST: send `POST <REST_API_URL>/tools/<tool name>` with the tool arguments as a JSON body. Use `Authorization: Bearer $MNEMOSYNE_TOKEN`.

If you cannot call the tools, use the `mnemosyne-connect` skill.

Your token name is your author name. The server records it on every memory you write. Do not send `author_id`. The server rejects a different value.

## The rules in short

1. Recall before you answer or act, when the topic can have history.
2. Store only durable facts. Never store secrets.
3. Write one fact per memory. Make it declarative, self-contained and dated.
4. Recall first, then update or invalidate. Do not duplicate.
5. Keep working notes in the scratchpad, not in memories.
6. If the server fails, continue without memory and tell the user.

## 1. Recall before you act

Call `mnemosyne_recall` at the start of a session. Call it again when the user names a person, project, client, tool or decision that you do not know.

Recall in these cases:

- The user says "like last time", "as before", "remember when" or "you know my".
- The user asks for something that depends on a preference or a past decision.
- You are about to ask the user a question that they may have answered before.
- You start work on a project that you may have seen before.

Do not recall for a question that is only about general knowledge.

Rules for recall:

- Write the query as a short natural phrase, for example `deployment preferences for the website project`.
- Use `limit` 5 for a normal lookup. Use 10 to 20 for a broad review.
- Add `temporal_weight` 0.2 when the newest facts matter most.
- If the first query returns nothing useful, try one more query with other words. Then stop.
- If you use a memory in your answer, say so. Name the memory id when the user asks where a fact came from.
- If a recalled fact conflicts with what the user says now, trust the user. Then fix the memory (see section 6).
- Recall is not proof. A memory can be old. Check `valid_until` and the date in the text.

## 2. What to remember

Store a memory when you learn one of these:

- A preference ("I prefer short answers").
- A decision and its reason.
- A stable fact about the user, a project, a client or a tool.
- A correction of something you said or stored before.
- A commitment with an owner and a date.

Do not store:

- Secrets: passwords, API keys, tokens, private keys, recovery phrases, card numbers.
- Transient task progress ("I fixed bug 12", "step 3 is done").
- Raw tool output, logs, stack traces or long pasted text.
- Anything the user asks you to keep private or to forget.
- Guesses that you cannot label as inferred.

If the user asks you to forget something, find it with `mnemosyne_recall`. Then call `mnemosyne_forget` with the exact `memory_id`. Confirm what you removed.

If a write returns `"status": "filtered"`, the server refused the content as noise or as a secret. Do not retry with other words.

## 3. How to write a memory

- One fact in each memory.
- Use a declarative sentence. Write "The user prefers metric units", not "Always use metric units".
- Make it self-contained. A reader with no context must understand it. Use names, not "he" or "it".
- Put the date in the text for facts that change. Use the form `2026-10-27`.
- Keep it under 300 characters.

Example call:

```json
{
  "content": "On 2026-10-27 the user chose Postgres over MySQL for the billing service because the team already runs Postgres.",
  "importance": 0.8,
  "source": "decision",
  "veracity": "stated"
}
```

### Importance bands

| Importance | Use for                                                    |
| ---------- | ---------------------------------------------------------- |
| 0.9 to 1.0 | Identity-level facts: name, role, core workflow            |
| 0.7 to 0.8 | Preferences, corrections, decisions, commitments           |
| 0.5        | Normal project and domain facts (the default)              |
| 0.3        | Low-value context that may help once                       |

### Veracity

Set `veracity` on every write.

| Value      | Use when                                   |
| ---------- | ------------------------------------------ |
| `stated`   | The user said it directly                  |
| `tool`     | A deterministic tool produced it           |
| `inferred` | You derived it. Say so in the text.        |
| `imported` | It came from an import                     |
| `unknown`  | The default. It gets no recall boost.      |

### Time-bound facts

Set `valid_until` (`YYYY-MM-DD`) for a fact that ends on a known date. Examples are a trial, a deadline or a temporary address.

## 4. Scope

The default scope on this server is `global`. A global memory is visible in every later session. Use it for almost everything.

Use `"scope": "session"` only for context that matters in this conversation alone.

## 5. Update, do not duplicate

Before you write, recall the topic. Then choose one action:

| Situation                                      | Action                                                              |
| ---------------------------------------------- | ------------------------------------------------------------------- |
| The same fact exists and is still true         | Do nothing                                                          |
| The fact exists and needs a small fix          | `mnemosyne_update` with `memory_id` and the new `content`           |
| The fact is no longer true and a new one exists | `mnemosyne_remember` the new fact. Then `mnemosyne_invalidate` the old id with `replacement_id` set to the new id. |
| The fact is wrong and has no replacement       | `mnemosyne_invalidate` with the old id                              |
| The user asks to delete it                     | `mnemosyne_forget`                                                  |
| The user confirms that a fact is right         | `mnemosyne_validate` with `action` `attest` and a short `note`      |

`mnemosyne_update` changes only `content` and `importance`.

Use `invalidate` for facts that were true once. This keeps the history. Use `forget` only when the user wants the memory gone.

## 6. Conflicts

If two memories conflict:

1. Fetch both with `mnemosyne_get`.
2. Ask the user which one is right, when you cannot tell.
3. Invalidate the wrong one. Set `replacement_id` to the right one.
4. Use `mnemosyne_validate` with `action` `attest` on the right one, and add a `note`.

## 7. Canonical facts for the user profile

Use canonical facts for stable profile data. Each fact has a `category` and a `name`. A new value replaces the old value, and the old value stays in history.

```json
{ "category": "identity", "name": "timezone", "body": "Europe/Berlin" }
```

- Write with `mnemosyne_remember_canonical`.
- Read one fact with `mnemosyne_recall_canonical` and `category` plus `name`.
- List a category with `category` only. Search with `query`.
- Retire a fact with `mnemosyne_forget_canonical`.

Use the categories `identity`, `preference` and `voice`. The profile is shared by all agents on this server.

## 8. Triples for relationships and dated facts

A triple is `subject`, `predicate`, `object`. Use triples for relationships between named things and for facts that change over time.

```json
{ "subject": "Acme GmbH", "predicate": "has_contract", "object": "Support plan 2026", "valid_from": "2026-01-01" }
```

Rules:

- Use `mnemosyne_triple_query` with `subject`, `predicate` or `object`. Add `as_of` to see the state on a date.
- Adding a triple closes the open triple with the same `subject` and `predicate`. A predicate holds one value at a time for one subject. This server ignores the `supersede` and `valid_until` arguments.
- For a relation with many values, use a different predicate for each value, for example `has_contract_support` and `has_contract_hosting`.
- Do not use the predicates `mentions`, `fact`, `occurred_on` or `has_source`. The server stores them in a different table.
- Write the same fact as a memory too when you need it in natural-language recall.

## 9. Batch writes

When you write more than two memories at once, use `mnemosyne_batch`. The batch is atomic. One failure rolls back all of it. A batch holds 50 operations at most. The actions are `remember`, `update`, `forget` and `invalidate`.

Use `"dry_run": true` first for a large batch.

## 10. Banks

A bank is a separate store of memories. Pass `bank` on every call that should not use the default bank. This includes recall.

- `default` is the shared brain. Put personal and general facts here.
- Use a named bank for one business domain or project: `business`, `clients`, `project-<name>`.
- Use letters, digits, hyphens and underscores in bank names. Use 64 characters at most.
- Recall reads one bank at a time. When a task spans two banks, recall in both.

Banks separate data. They do not control access. Every agent with a valid token can read and write every bank. Do not put a secret in a bank because you think it is hidden.

## 11. Scratchpad

Use the scratchpad for working notes that you need for this task only. Examples are a plan, a checklist or a draft.

- Write with `mnemosyne_scratchpad_write`.
- Read with `mnemosyne_scratchpad_read`.
- Clear with `mnemosyne_scratchpad_clear` when the task ends.

Move a result into a memory only if it is a durable fact.

## 12. Maintenance

The server never consolidates by itself. It does so only when a client calls `mnemosyne_sleep`. Sleep needs no LLM.

| When                                              | Call                                             |
| ------------------------------------------------- | ------------------------------------------------ |
| End of a long session with many new memories      | `mnemosyne_sleep`                                |
| Weekly, or after a large import                   | `mnemosyne_sleep` with `all_sessions` true       |
| Before a risky sleep on a large store             | `mnemosyne_sleep` with `dry_run` true            |
| Weekly, or when recall returns noise              | `mnemosyne_hygiene_audit`                        |

Do not set `force` unless the user asks. It skips the age threshold.

Hygiene steps:

1. Call `mnemosyne_hygiene_audit`. It only reads.
2. Show the user the candidates in `report.candidates`.
3. After the user agrees, call `mnemosyne_hygiene_clean` with `candidates_json` set to the JSON text of the agreed candidates. Leave `confirm` false first. That is a dry run.
4. Call it again with `confirm` true. Prefer `action` `archive` to `delete`. Archive can be undone. Delete cannot.
5. Never delete a candidate that has `secret_flags` without telling the user. Tell the user to rotate the secret.

Use `mnemosyne_stats` to see the size of the store.

## 13. Failures

| Result                                  | What to do                                                              |
| --------------------------------------- | ----------------------------------------------------------------------- |
| HTTP 401                                | The token is wrong or revoked. Tell the user. Use `mnemosyne-connect`.  |
| HTTP 421 on `/mcp`                      | The address is not allowed. Tell the user to use an address from Connection Details. |
| Connection refused or timeout           | The server is stopped. Continue without memory. Tell the user.          |
| HTTP 503 from `/healthz`                | The server cannot open its database. Continue without memory. Tell the user. |
| `"status": "not_found"`                 | The id is wrong or the bank is wrong. Check `bank`.                     |
| `"status": "filtered"`                  | The content was refused. Do not retry.                                  |

When the server fails, do not stop the user's task. Say once that memory is not available. Do not claim that you stored or recalled anything.

## Checklist before you write

- Is it durable? Is it free of secrets?
- Did I recall first? Is this a duplicate?
- Is it one fact, with a date, in plain words?
- Did I set `importance` and `veracity`?
- Is the `bank` right?
