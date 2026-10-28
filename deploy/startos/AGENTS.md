# AGENTS.md

- This package lives in `deploy/startos/` of an upstream fork, and the image builds from the repository root (`dockerBuild.workdir: '../..'`). Paths in the Dockerfile are relative to the root, and `Dockerfile.dockerignore` replaces the root `.dockerignore`.
- Never edit `mnemosyne/` for a packaging need. It is upstream code, and any change there conflicts on every upstream merge. Wrap it in `server/mnemosyne_startos/` instead.
- The server imports private helpers from `mnemosyne.mcp_server`, `mnemosyne.mcp_tools` and `mnemosyne.core.banks`. Check them on every upstream merge (the list is in `UPDATING.md`).
- Test the server with `pip install -e "../..[mcp,test]" -e server && cd server && MNEMOSYNE_NO_EMBEDDINGS=1 pytest`, run from `deploy/startos/`.
