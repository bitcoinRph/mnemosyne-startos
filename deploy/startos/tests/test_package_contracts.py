import json
import os
import re
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_image_contract_uses_entrypoint_and_keeps_data_root_owned():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    runtime = dockerfile.split("FROM python:3.12-slim")[-1]
    dockerignore = (ROOT / "Dockerfile.dockerignore").read_text(encoding="utf-8")
    entrypoint = (ROOT / "docker-entrypoint.sh").read_text(encoding="utf-8")
    assert "!deploy/startos/docker-entrypoint.sh" in dockerignore
    assert "apt-get install -y --no-install-recommends gosu" in runtime
    assert 'ENTRYPOINT ["mnemosyne-startos-entrypoint"]' in runtime
    assert 'DATA_ROOT="${MNEMOSYNE_DATA_ROOT:-/data}"' in entrypoint
    assert 'if [ -L "$path" ] || { [ -e "$path" ] && [ ! -d "$path" ]; }; then' in entrypoint
    assert "install -d -o 0 -g 0 -m 0755 \"$DATA_ROOT\"" in entrypoint
    assert "chown 0:0 \"$DATA_ROOT\"" in entrypoint
    assert "chmod 0755 \"$DATA_ROOT\"" in entrypoint
    assert "chown -R -h 10001:10001" in entrypoint
    assert not re.search(r"^chown -R (?!-h )10001:10001", entrypoint, re.MULTILINE)
    assert not re.search(r'^chown -R -h 10001:10001 "?\$DATA_ROOT"?$', entrypoint, re.MULTILINE)
    assert 'exec gosu 10001:10001 "$@"' in entrypoint
    assert "MNEMOSYNE_BACKUP_DIR=/data/backups" in runtime


def test_entrypoint_rejects_top_level_symlink_before_mutating_referent(tmp_path):
    data_root = tmp_path / "data"
    outside = tmp_path / "outside"
    data_root.mkdir()
    outside.mkdir()
    outside.chmod(0o711)
    (data_root / "home").symlink_to(outside, target_is_directory=True)
    before = stat.S_IMODE(outside.stat().st_mode)

    env = {**os.environ, "MNEMOSYNE_DATA_ROOT": str(data_root)}
    result = subprocess.run(
        ["sh", str(ROOT / "docker-entrypoint.sh"), "true"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "refusing unsafe data path" in result.stderr
    assert stat.S_IMODE(outside.stat().st_mode) == before


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


def test_release_critical_contracts_are_ci_gates():
    workflow = (ROOT.parents[1] / ".github/workflows/startos.yml").read_text(
        encoding="utf-8"
    )
    assert "package-contracts:" in workflow
    assert "pytest tests/test_package_contracts.py" in workflow
    assert "runs-on: ubuntu-24.04" in workflow
    assert "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020" in workflow
    assert "node-version: '26.13.0'" in workflow
    assert "python-version: '3.12.14'" in workflow
    assert "python -m pip install pytest==9.2.0" in workflow
    assert "npm run test:contracts" in workflow
    assert "npm run check" in workflow
    assert "needs: [server-tests, package-contracts]" in workflow


def test_node_contract_tooling_is_declared_and_script_policy_is_explicit():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))

    assert package["devDependencies"] == {
        "tsx": "4.23.15",
        "typescript": "6.0.3",
    }
    assert package["allowScripts"] == {"esbuild": True}
    assert lock["packages"][""]["devDependencies"] == package["devDependencies"]
