import json

import pytest

import mnemosyne

from mnemosyne_startos.app import build_app

ALICE = {"Authorization": "Bearer alice-secret"}
BOB = {"Authorization": "Bearer bob-secret"}

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}
MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}


def test_healthz_needs_no_auth(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": mnemosyne.__version__}


def test_openapi_needs_no_auth(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    doc = r.json()
    assert doc["openapi"].startswith("3.1")
    assert doc["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    assert "/api/v1/memories/{memory_id}" in doc["paths"]
    remember = doc["components"]["schemas"]["Args_mnemosyne_remember"]
    assert "content" in remember["properties"]
    assert "memory_id" not in doc["components"]["schemas"]["UpdateBody"]["properties"]
    assert "mnemosyne_recall" in doc["paths"]["/api/v1/tools/{name}"]["post"][
        "parameters"
    ][0]["schema"]["enum"]


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/tools"),
        ("POST", "/api/v1/memories"),
        ("POST", "/api/v1/recall"),
        ("GET", "/api/v1/stats"),
        ("DELETE", "/api/v1/memories/x"),
        ("GET", "/api/v1/nope"),
    ],
)
def test_rest_requires_token(client, method, path):
    assert client.request(method, path).status_code == 401
    wrong = client.request(method, path, headers={"Authorization": "Bearer nope"})
    assert wrong.status_code == 401


def test_rest_round_trip(client):
    r = client.post(
        "/api/v1/memories",
        headers=ALICE,
        json={"content": "The deploy key lives in the blue safe", "importance": 0.8},
    )
    assert r.status_code == 200, r.text
    stored = r.json()
    assert stored["status"] == "stored"
    memory_id = stored["memory_id"]

    r = client.post(
        "/api/v1/recall", headers=ALICE, json={"query": "deploy key safe", "limit": 3}
    )
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert any(memory_id == item.get("id") for item in results), results

    r = client.get(f"/api/v1/memories/{memory_id}", headers=ALICE)
    assert r.status_code == 200
    assert "blue safe" in json.dumps(r.json()["memory"])

    r = client.patch(
        f"/api/v1/memories/{memory_id}",
        headers=ALICE,
        json={"content": "The deploy key lives in the red safe"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "updated"
    assert "red safe" in json.dumps(
        client.get(f"/api/v1/memories/{memory_id}", headers=ALICE).json()
    )

    assert client.get("/api/v1/stats", headers=ALICE).status_code == 200

    r = client.delete(f"/api/v1/memories/{memory_id}", headers=ALICE)
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

    assert client.get(f"/api/v1/memories/{memory_id}", headers=ALICE).status_code == 404
    assert (
        client.delete(f"/api/v1/memories/{memory_id}", headers=ALICE).status_code == 404
    )
    assert (
        client.patch(
            f"/api/v1/memories/{memory_id}", headers=ALICE, json={"content": "x"}
        ).status_code
        == 404
    )


def test_author_is_token_name(client):
    ids = {}
    for who, headers in (("alice", ALICE), ("bob", BOB)):
        r = client.post(
            "/api/v1/memories",
            headers=headers,
            json={"content": f"note written by {who} about quasar telemetry"},
        )
        ids[who] = r.json()["memory_id"]
    for who, memory_id in ids.items():
        memory = client.get(f"/api/v1/memories/{memory_id}", headers=ALICE).json()[
            "memory"
        ]
        assert memory["author_id"] == who, memory


def test_spoofed_author_is_rejected(client):
    r = client.post(
        "/api/v1/memories",
        headers=ALICE,
        json={"content": "spoof", "author_id": "bob"},
    )
    assert r.status_code == 400
    assert "bob" in r.json()["error"]


def test_generic_tool_endpoint(client):
    listed = client.get("/api/v1/tools", headers=ALICE).json()["tools"]
    assert "mnemosyne_remember" in {t["name"] for t in listed}

    r = client.post(
        "/api/v1/tools/mnemosyne_remember",
        headers=ALICE,
        json={"content": "generic endpoint memory"},
    )
    assert r.status_code == 200 and r.json()["status"] == "stored"

    r = client.post("/api/v1/tools/mnemosyne_stats", headers=ALICE)
    assert r.status_code == 200


def test_unknown_tool_is_404(client):
    r = client.post("/api/v1/tools/mnemosyne_nope", headers=ALICE, json={})
    assert r.status_code == 404
    assert "error" in r.json()


def test_bad_arguments_are_400(client):
    missing = client.post("/api/v1/memories", headers=ALICE, json={})
    assert missing.status_code == 400 and "content" in missing.json()["error"]
    not_json = client.post("/api/v1/memories", headers=ALICE, content=b"{nope")
    assert not_json.status_code == 400
    not_object = client.post("/api/v1/memories", headers=ALICE, json=[1])
    assert not_object.status_code == 400


def test_mcp_requires_token(client):
    r = client.post("/mcp", headers=MCP_HEADERS, json=INIT)
    assert r.status_code == 401


def test_mcp_initialize_reaches_mcp_app(client):
    r = client.post("/mcp", headers={**MCP_HEADERS, **ALICE}, json=INIT)
    assert r.status_code == 200, r.text
    assert "mnemosyne" in r.text


def test_mcp_rejects_unlisted_host(client):
    r = client.post(
        "/mcp", headers={**MCP_HEADERS, **ALICE, "Host": "evil.example"}, json=INIT
    )
    assert r.status_code == 421


@pytest.mark.parametrize("value", [None, "", "   "])
def test_refuses_to_start_without_tokens(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("MNEMOSYNE_MCP_TOKENS")
    else:
        monkeypatch.setenv("MNEMOSYNE_MCP_TOKENS", value)
    with pytest.raises(RuntimeError, match="MNEMOSYNE_MCP_TOKENS"):
        build_app(host="0.0.0.0")
