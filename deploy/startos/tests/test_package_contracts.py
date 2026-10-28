from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_image_contract_uses_entrypoint_and_keeps_data_root_owned():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    runtime = dockerfile.split("FROM python:3.12-slim")[-1]
    dockerignore = (ROOT / "Dockerfile.dockerignore").read_text(encoding="utf-8")
    entrypoint = (ROOT / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert "!deploy/startos/docker-entrypoint.sh" in dockerignore
    assert "apt-get install -y --no-install-recommends gosu" in runtime
    assert 'ENTRYPOINT ["mnemosyne-startos-entrypoint"]' in runtime
    assert "install -d -o 0 -g 0 -m 0755 /data" in entrypoint
    assert "chown 0:0 /data" in entrypoint
    assert "chmod 0755 /data" in entrypoint
    assert "chown -R 10001:10001 /data/backups /data/home /data/mnemosyne" in entrypoint
    assert not re.search(r"^chown -R 10001:10001 /data$", entrypoint, re.MULTILINE)
    assert 'exec gosu 10001:10001 "$@"' in entrypoint
    assert "MNEMOSYNE_BACKUP_DIR=/data/backups" in runtime


def test_package_version_and_architectures_are_preserved():
    version = (ROOT / "startos/versions/current.ts").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "version: '4.0.0-beta.6:0'" in version
    assert re.search(r"^ARCHES := x86 arm$", makefile, re.MULTILINE)


def test_startos_passes_backup_directory_to_runtime():
    main = (ROOT / "startos/main.ts").read_text(encoding="utf-8")
    assert "MNEMOSYNE_BACKUP_DIR: '/data/backups'" in main


def test_startos_invokes_image_entrypoint_instead_of_plain_command_array():
    main = (ROOT / "startos/main.ts").read_text(encoding="utf-8")
    assert "command: sdk.useEntrypoint([" in main
    assert not re.search(r"command:\s*\[", main)


def test_store_init_only_seeds_an_absent_file_and_never_repairs_malformed_state():
    seed = (ROOT / "startos/init/seedStore.ts").read_text(encoding="utf-8")
    assert ".read().once()" in seed
    assert ".write(effects, { tokens: {} })" in seed
    assert ".merge(" not in seed