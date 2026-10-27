# Updating the upstream version

The package wraps a fork of Mnemosyne. Upstream is `mnemosyne-oss/mnemosyne` on GitHub. This repository (`bitcoinRph/mnemosyne-startos`) is the fork. The package lives in `deploy/startos/`, and the image is built from the repository root.

No image tag or submodule pins upstream. The pin is the fork commit that the build checks out. The Mnemosyne version is the `__version__` string in `mnemosyne/__init__.py` at that commit.

## Determining the upstream version

1. Read the version the fork carries now:

   ```bash
   grep __version__ mnemosyne/__init__.py
   ```

2. Read the newest upstream release:

   ```bash
   gh release view -R mnemosyne-oss/mnemosyne --json tagName -q .tagName
   ```

3. If the two differ, the fork is behind. Upstream is a beta line, so read the upstream changelog before you merge.

Upstream writes versions in the Python form, for example `4.0.0b6`. ExVer needs the dotted prerelease form, `4.0.0-beta.6`. Keep the prerelease suffix. Do not drop it, because a beta must sort below the stable release.

| Upstream form | ExVer upstream part |
| ------------- | ------------------- |
| `4.0.0b6`     | `4.0.0-beta.6`      |
| `4.0.0rc1`    | `4.0.0-rc.1`        |
| `4.0.0`       | `4.0.0`             |

## Applying the bump

1. Create a branch from `main` in the fork.
2. Merge the upstream release into the fork:

   ```bash
   git remote add upstream https://github.com/mnemosyne-oss/mnemosyne.git
   git fetch upstream --tags
   git merge <upstream-tag>
   ```

   Use a merge commit. Do not rebase or squash. A rebase makes the next upstream merge conflict again.
3. Do not edit anything under `mnemosyne/` to fix a packaging problem. Fix it in `deploy/startos/server/`. If you must resolve a merge conflict inside `mnemosyne/`, keep the upstream side.
4. Check that the private upstream names that the server imports still exist. The server is `deploy/startos/server/mnemosyne_startos/app.py`. Run this check:

   ```bash
   grep -n "_BearerTokenMiddleware\|_build_streamable_http_app\|_resolve_multi_tokens" mnemosyne/mcp_server.py
   grep -n "def _create_instance\|def handle_tool_call\|def get_tool_definitions" mnemosyne/mcp_tools.py
   grep -n "def get_bank_db_path_read_only" mnemosyne/core/banks.py
   ```

   Each name must appear. The server imports these names:

   - `mnemosyne.mcp_server`: `_BearerTokenMiddleware`, `_build_streamable_http_app`, `_resolve_multi_tokens`
   - `mnemosyne.mcp_tools`: `_create_instance`, `handle_tool_call`, `get_tool_definitions`
   - `mnemosyne.core.banks`: `get_bank_db_path_read_only`

   If a name moved or changed its arguments, change `app.py` to match. Also check that the Bearer middleware still sets the author from the token name, and that `MNEMOSYNE_MCP_ALLOWED_HOSTS` is still the Host allowlist variable.
5. Run the server tests:

   ```bash
   pip install -e "../..[mcp,test]" -e server
   cd server && MNEMOSYNE_NO_EMBEDDINGS=1 pytest
   ```

   Run both commands from `deploy/startos/`. All tests must pass. CI runs the same tests from the repository root.
6. Compare the tool list. Open `mnemosyne/tool_schemas.py` and `mnemosyne/mcp_tools.py`. Count the tools in `_TOOL_HANDLERS`. If the count or a tool name changed, update the tool counts and names in `README.md` and in the `skills/` folder of the repository.
7. Set the version in `startos/versions/current.ts`. Put the upstream version before the colon and `0` after it. For example, use `4.0.0-beta.7:0`. Keep the prerelease suffix while upstream is a prerelease. Update `releaseNotes` in all five languages.
8. For a package-only change with no new upstream release, keep the upstream part and raise the number after the colon by one, for example `4.0.0-beta.6:1`.
9. Run `npm run check` in `deploy/startos/`.
10. Push the branch and open a pull request. The CI workflow `.github/workflows/startos.yml` runs the server tests and builds the `.s9pk` for x86 and for arm. Both builds must pass.
11. Install the x86 build on a test StartOS server. Add a token. Call `mnemosyne_stats` from a client. Do not install on a live server without approval.

## Build notes

- The Dockerfile downloads the embedding model `BAAI/bge-small-en-v1.5` from Hugging Face at build time. The build host and the CI runner need network access to Hugging Face. The running service is offline.
- If upstream changes the default embedding model or its cache layout, change the bake step in `Dockerfile` so that the model sits where `MNEMOSYNE_FASTEMBED_CACHE_DIR` points. A vector table has a fixed size, so a database made with one model cannot use another model without a reindex. Read `docs/migration-4.0.md` in the fork before you release such a change.
- The build context is the repository root. `deploy/startos/Dockerfile.dockerignore` replaces the root `.dockerignore` for this build. If you add a file that the image needs, make sure the ignore file does not exclude it.
