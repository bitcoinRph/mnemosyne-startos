import json
from pathlib import Path

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


def test_healthz_hides_exception_details(client, monkeypatch):
    from mnemosyne_startos import app

    monkeypatch.setattr(
        app,
        "_probe_default_bank",
        lambda: (_ for _ in ()).throw(RuntimeError("sqlite secret path /data/private")),
    )
    r = client.get("/healthz")
    assert r.status_code == 503
    assert r.json() == {"status": "unavailable"}


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


@pytest.mark.parametrize(
    "path",
    [
        "../escape.json",
        "nested/../../escape.json",
        "/data/backups/absolute.json",
        "/data/mnemosyne/shared/mnemosyne.db",
    ],
)
def test_rest_export_rejects_paths_outside_backup_dir(client, path):
    r = client.post(
        "/api/v1/tools/mnemosyne_export",
        headers=ALICE,
        json={"output_path": path},
    )
    assert r.status_code == 400
    assert "backup" in r.json()["error"].lower()


def test_rest_export_resolves_relative_path_inside_backup_dir(client, backup_dir):
    r = client.post(
        "/api/v1/tools/mnemosyne_export",
        headers=ALICE,
        json={"output_path": "exports/rest.json"},
    )
    assert r.status_code == 200, r.text
    assert (Path(backup_dir) / "exports" / "rest.json").is_file()


def test_mcp_handler_uses_same_backup_path_guard(backup_dir):
    build_app(host="0.0.0.0")
    import mnemosyne.mcp_server as mcp_server

    with pytest.raises(ValueError, match="backup"):
        mcp_server.handle_tool_call(
            "mnemosyne_import", {"input_path": "../outside.json"}
        )

    source = Path(backup_dir) / "imports" / "mcp.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('{"schema_version":"invalid-test"}', encoding="utf-8")
    with pytest.raises(Exception) as exc_info:
        mcp_server.handle_tool_call(
            "mnemosyne_import", {"input_path": "imports/mcp.json", "dry_run": True}
        )
    assert "backup" not in str(exc_info.value).lower()


def test_whitespace_provider_cannot_bypass_file_import_guard():
    build_app(host="0.0.0.0")
    import mnemosyne.mcp_server as mcp_server

    with pytest.raises(ValueError, match="backup"):
        mcp_server.handle_tool_call(
            "mnemosyne_import",
            {"provider": "   ", "input_path": "../outside.json"},
        )


@pytest.mark.parametrize(
    "tool,path_key",
    [("mnemosyne_export", "output_path"), ("mnemosyne_import", "input_path")],
)
def test_backup_guard_rejects_symlinked_components_and_targets(
    backup_dir, tool, path_key
):
    build_app(host="0.0.0.0")
    import mnemosyne.mcp_server as mcp_server

    root = Path(backup_dir)
    root.mkdir(parents=True, exist_ok=True)
    outside = root.parent / "outside"
    outside.mkdir(exist_ok=True)
    component = root / "linked-dir"
    target = root / "linked-file.json"
    if not component.exists() and not component.is_symlink():
        component.symlink_to(outside, target_is_directory=True)
    if not target.exists() and not target.is_symlink():
        target.symlink_to(outside / "file.json")

    for path in ("linked-dir/file.json", "linked-file.json"):
        with pytest.raises(ValueError, match="symlink"):
            mcp_server.handle_tool_call(tool, {path_key: path})


def test_export_rejects_hard_link_target_without_overwriting_source(backup_dir):
    build_app(host="0.0.0.0")
    import mnemosyne.mcp_server as mcp_server

    root = Path(backup_dir)
    root.mkdir(parents=True, exist_ok=True)
    source = root.parent / "database.db"
    source.write_text("database-bytes", encoding="utf-8")
    target = root / "database-backup.json"
    target.unlink(missing_ok=True)
    target.hardlink_to(source)

    with pytest.raises(ValueError, match="hard link"):
        mcp_server.handle_tool_call(
            "mnemosyne_export", {"output_path": "database-backup.json"}
        )
    assert source.read_text(encoding="utf-8") == "database-bytes"


def test_export_does_not_follow_target_swapped_to_symlink(
    backup_dir, monkeypatch
):
    from mnemosyne_startos import app

    root = Path(backup_dir)
    target = root / "race" / "export.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    outside = root.parent / "outside-race-target"
    outside.write_text("outside-bytes", encoding="utf-8")

    def swap_target_and_write(name, arguments):
        target.unlink(missing_ok=True)
        target.symlink_to(outside)
        Path(arguments["output_path"]).write_text("export-bytes", encoding="utf-8")
        return {"status": "exported", "path": arguments["output_path"]}

    monkeypatch.setattr(app, "_upstream_handle_tool_call", swap_target_and_write)
    with pytest.raises(ValueError, match="symlink"):
        app.handle_tool_call("mnemosyne_export", {"output_path": "race/export.json"})
    assert outside.read_text(encoding="utf-8") == "outside-bytes"


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
