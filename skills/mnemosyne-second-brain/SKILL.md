---
name: mnemosyne-second-brain
description: Business and knowledge-work workflows on top of Mnemosyne long-term memory. Use it when the user wants a "second brain". Use it when the user asks "what do we know about" a client, project or topic. Use it to capture a decision, meeting notes, an action item, a client, a contact, a vendor, an SOP or a how-to. Use it for daily and weekly reviews, conflicting facts, imports of existing notes and exports for audit. It stores decisions with reasons, models clients as entities with dated triples, and answers with cited memory ids. Read the mnemosyne-memory skill first.
license: MIT
---

# Mnemosyne second brain

This skill adds business workflows to the `mnemosyne-memory` skill. Follow that skill for recall, writing rules, importance, veracity, banks and failures. The tool list is in `../mnemosyne-memory/references/tools.md`.

## Set up the banks

| Bank              | Content                                                   |
| ----------------- | --------------------------------------------------------- |
| `default`         | The shared brain: the user, preferences, general facts    |
| `business`        | The company: strategy, policies, SOPs, vendors, finances  |
| `clients`         | Clients, contacts, contracts, history with each client    |
| `project-<name>`  | One bank for each project, for example `project-website`  |

Pass `bank` on every call to a named bank. Banks do not control access. Every agent can read all of them.

Store facts about people only when they help the work. Do not store private details that the user did not give you for this purpose. Never store secrets.

## Name things the same way every time

Before you create an entity, recall its name. Use one spelling, for example `Acme GmbH`. Put the full name in every memory and every triple. This lets recall and `triple_query` find the same entity.

## Capture a decision

Write one memory for each decision. Include these parts in one or two sentences:

1. The date.
2. What was decided.
3. The reason.
4. The alternatives that the team rejected, when they matter.
5. Who decided.

Set `importance` 0.8, `source` `decision` and `veracity` `stated`. Use the bank of the project.

When a decision replaces an older one, write the new decision. Then call `mnemosyne_invalidate` on the old id with `replacement_id`. Link them with `mnemosyne_graph_link` and the relationship `supersedes` when the history matters.

## Turn meeting notes into memories

1. Read the notes. Do not store the notes as one block.
2. List the facts, decisions and action items.
3. Skip small talk and anything the user marked as private.
4. Write each item as its own memory. Use one `mnemosyne_batch` call. Use `dry_run` first when the batch has more than 10 items.
5. Put the meeting date and the meeting name in `metadata`.
6. For an action item, write the owner, the task and the due date in the text. Set `valid_until` to the due date. Use `importance` 0.7 and `source` `task`.
7. When the task is done, call `mnemosyne_invalidate` on its id. Do this when the user reports it.
8. Reply with a short list of what you stored, with the ids.

## Clients, contacts and vendors

Use two layers:

- A memory for the description. For example: "Acme GmbH is a logistics client in Hamburg. The contact is Jana Weber, head of IT." Use `importance` 0.6.
- Triples for the relationships and the dates.

Triple patterns:

| Subject         | Predicate         | Object                |
| --------------- | ----------------- | --------------------- |
| Acme GmbH       | has_contact       | Jana Weber            |
| Acme GmbH       | has_contract      | Support plan 2026     |
| Acme GmbH       | account_owner     | Tom Ruiz              |
| Jana Weber      | works_at          | Acme GmbH             |
| Northwind Ltd   | supplies          | Server hosting        |

Set `valid_from` on every triple that can change. A new triple with the same subject and predicate closes the old one. This matches single-valued facts such as `account_owner`. For a client with several contracts, use a different predicate for each, for example `has_contract_support` and `has_contract_hosting`.

To end a relationship with no replacement, add a triple with the object `none` and today's date in `valid_from`.

## Projects

Use the bank `project-<name>`. Store these items:

- The goal, the owner and the deadline.
- Decisions and their reasons.
- Milestones and risks.
- Open action items (with `valid_until`).

At the end of a project, write one summary memory. Then run `mnemosyne_sleep` on that bank.

## SOPs and how-tos

Write one memory for each procedure. Start with a title. Number the steps. Keep each procedure under 1000 characters. For a longer procedure, write one memory for each part and start each with the same title.

Set `source` `sop`, `importance` 0.7 and `bank` `business`. To change a step, recall the SOP and call `mnemosyne_update`. Do not write a second copy.

## Answer "what do we know about X"

1. Recall X in each bank that can hold it. Use `limit` 10.
2. Call `mnemosyne_triple_query` with `subject` X, then with `object` X.
3. For the best hit, call `mnemosyne_graph_query` with `seed_memory_id` to find linked memories.
4. Call `mnemosyne_recall_canonical` if X is the user or the company.
5. Write the answer in short groups: facts, relationships, open items.
6. Cite the memory id after each fact, for example `(mem 3f9a...)`.
7. Mark old or uncertain facts. Give the date.
8. Say what you did not find. Do not guess.

## Daily and weekly review

Daily, at the end of work:

1. Recall `action items due` with `temporal_weight` 0.3. List open items and due dates.
2. Invalidate items that the user says are done.
3. Store new decisions and facts from the day.

Weekly:

1. Run the daily steps.
2. Call `mnemosyne_sleep` with `all_sessions` true for each active bank.
3. Call `mnemosyne_hygiene_audit` for each active bank. Follow the hygiene steps in the `mnemosyne-memory` skill.
4. Call `mnemosyne_stats` and report the size of each bank.
5. Write a short summary of the week as one memory in `business`.

## Conflicting facts

When two facts conflict:

1. Fetch both ids with `mnemosyne_get`. Read the dates and the sources.
2. If the user can tell you which is right, ask one short question.
3. Call `mnemosyne_invalidate` on the wrong one with `replacement_id`.
4. Call `mnemosyne_validate` with `action` `attest` on the right one. Add a `note` that gives the reason and the date.

If you cannot decide, keep both. Tell the user. Do not delete either.

## Import existing notes

- The file import (`input_path`) accepts only a JSON file from `mnemosyne_export`. The file must be inside the server container.
- To import another provider, call `mnemosyne_import` with `provider` `hindsight` or `mem0`, an `api_key` and `dry_run` true first.
- To import plain notes, split them into facts yourself. Write them with `mnemosyne_batch`, 50 items at most per call. Set `veracity` `imported` and `source` to the note name.
- Check the count with `mnemosyne_stats` after the import. Then run `mnemosyne_hygiene_audit`.

## Export for audit

Call `mnemosyne_export` with `output_path` set to a file under `/data/backups/`, for example `/data/backups/audit-2026-10-27.json`. The file stays inside the server. Tell the user the path. The user can read it with `start-cli package attach` or restore it from a StartOS backup. Export one bank at a time with `bank`.

## Worked examples

### 1. Record a decision

```json
{
  "tool": "mnemosyne_batch",
  "arguments": {
    "bank": "project-website",
    "operations": [
      {
        "action": "remember",
        "content": "On 2026-10-27 the team chose Astro for the website because it ships no JavaScript by default. They rejected Next.js as too heavy. Decided by Maria Lopez.",
        "importance": 0.8,
        "source": "decision",
        "veracity": "stated"
      }
    ]
  }
}
```

Then link the decision to the project:

```json
{
  "tool": "mnemosyne_triple_add",
  "arguments": {
    "bank": "project-website",
    "subject": "Website project",
    "predicate": "uses_framework",
    "object": "Astro",
    "valid_from": "2026-10-27"
  }
}
```

### 2. Meeting notes to memories

```json
{
  "tool": "mnemosyne_batch",
  "arguments": {
    "bank": "clients",
    "operations": [
      {
        "action": "remember",
        "content": "On 2026-10-26 Acme GmbH asked to move the support plan renewal from January to March 2027.",
        "importance": 0.7,
        "veracity": "stated",
        "metadata": { "meeting": "Acme sync", "date": "2026-10-26" }
      },
      {
        "action": "remember",
        "content": "Action: Tom Ruiz sends the Acme GmbH renewal quote by 2026-11-05.",
        "importance": 0.7,
        "source": "task",
        "valid_until": "2026-11-05",
        "veracity": "stated",
        "metadata": { "meeting": "Acme sync", "owner": "Tom Ruiz" }
      }
    ]
  }
}
```

### 3. Answer "what do we know about Acme GmbH"

Make these calls in order:

```json
{ "tool": "mnemosyne_recall", "arguments": { "bank": "clients", "query": "Acme GmbH", "limit": 10 } }
{ "tool": "mnemosyne_triple_query", "arguments": { "bank": "clients", "subject": "Acme GmbH" } }
{ "tool": "mnemosyne_graph_query", "arguments": { "bank": "clients", "seed_memory_id": "<best hit id>", "max_hops": 2 } }
```

Then answer with facts, relationships and open items. Cite each memory id.

### 4. Fix a conflicting fact

The user says the Acme contact is now Ben Frost. Memory `m_old` says Jana Weber.

```json
{ "tool": "mnemosyne_remember", "arguments": { "bank": "clients", "content": "As of 2026-10-27 the Acme GmbH contact is Ben Frost, head of IT.", "importance": 0.7, "veracity": "stated" } }
{ "tool": "mnemosyne_invalidate", "arguments": { "bank": "clients", "memory_id": "m_old", "replacement_id": "<new id>" } }
{ "tool": "mnemosyne_triple_add", "arguments": { "bank": "clients", "subject": "Acme GmbH", "predicate": "has_contact", "object": "Ben Frost", "valid_from": "2026-10-27" } }
{ "tool": "mnemosyne_validate", "arguments": { "bank": "clients", "memory_id": "<new id>", "action": "attest", "note": "Confirmed by the user on 2026-10-27" } }
```
