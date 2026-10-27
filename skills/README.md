# Mnemosyne skills

These skills teach an AI agent to use a Mnemosyne memory server, for example the one from the StartOS package. They follow the Agent Skills format. Each skill is a folder with a `SKILL.md` file. The `name` field equals the folder name.

| Skill                                              | What it does                                                                                           |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [`mnemosyne-memory`](mnemosyne-memory/SKILL.md)    | The core protocol: when to recall, what to store, how to write a memory, banks, maintenance, failures. Install this first. The file `references/tools.md` lists all 30 tools. |
| [`mnemosyne-second-brain`](mnemosyne-second-brain/SKILL.md) | Business workflows: decisions, meeting notes, clients and vendors, SOPs, reviews, imports, exports. Needs `mnemosyne-memory`. |
| [`mnemosyne-connect`](mnemosyne-connect/SKILL.md)  | Connects an agent to the server and fixes connection errors. The file `references/clients.md` has the setup for each client. |

The skill `hermes-memory-providers` in this folder is a different skill. It installs Mnemosyne as a local Hermes memory provider. You do not need it to use the StartOS server.

## Install

Clone the repository once. Run the commands from its root. Copy the folders, or use `ln -s` to link them so that a `git pull` updates them.

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -r skills/mnemosyne-memory skills/mnemosyne-second-brain skills/mnemosyne-connect ~/.claude/skills/
```

For one project only, copy the folders to `.claude/skills/` in that project.

### Codex CLI, OpenClaw, and Hermes Agent (shared folder)

Codex and OpenClaw read `~/.agents/skills`. Hermes reads it when you list it in `skills.external_dirs`.

```bash
mkdir -p ~/.agents/skills
cp -r skills/mnemosyne-memory skills/mnemosyne-second-brain skills/mnemosyne-connect ~/.agents/skills/
```

For one repository only, copy the folders to `.agents/skills/` in that repository.

### Hermes Agent

Choose one of these ways.

- Add the shared folder to `~/.hermes/config.yaml`:

  ```yaml
  skills:
    external_dirs:
      - ~/.agents/skills
  ```

- Or copy the folders to `~/.hermes/skills/`.
- For a project folder (`.hermes/skills` or `.agents/skills`), run `hermes skills trust` once.

### OpenClaw

Copy the folders to one of these places:

- `<workspace>/skills`
- `<workspace>/.agents/skills`
- `~/.agents/skills`
- `~/.openclaw/skills`

### Codex CLI (own folder)

You can also use `~/.codex/skills` for the user, or `.agents/skills` in a repository.

## After you install

1. Connect the agent. Ask it to "connect to my Mnemosyne server", or see `mnemosyne-connect/references/clients.md`.
2. Ask the agent to call `mnemosyne_stats`. A JSON result means success.
3. Tell the agent: "Remember that I prefer short answers." Start a new session. Ask: "What do I prefer?"
