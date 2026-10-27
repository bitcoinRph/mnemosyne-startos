"""Environment is fixed before mnemosyne is imported: several of its modules
resolve the data directory at import time."""

import os
import tempfile

_DATA = tempfile.mkdtemp(prefix="mnemosyne-startos-test-")
os.environ["MNEMOSYNE_DATA_DIR"] = os.path.join(_DATA, "mnemosyne")
os.environ["MNEMOSYNE_HOME"] = os.path.join(_DATA, "home")
os.environ["HERMES_HOME"] = os.path.join(_DATA, "home", "hermes")
os.environ["MNEMOSYNE_SHARED_DB_PATH"] = os.path.join(_DATA, "mnemosyne", "shared.db")
os.environ["MNEMOSYNE_NO_EMBEDDINGS"] = "1"
os.environ["MNEMOSYNE_MCP_TOKENS"] = '{"alice": "alice-secret", "bob": "bob-secret"}'
os.environ["MNEMOSYNE_MCP_ALLOWED_HOSTS"] = "mnemo.test"

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from mnemosyne_startos.app import build_app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # Entering the context runs ASGI lifespan, which the MCP session manager needs.
    with TestClient(build_app(host="0.0.0.0"), base_url="http://mnemo.test") as c:
        yield c
