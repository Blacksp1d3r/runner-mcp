import json
import os
from pathlib import Path

import pytest

from runner_mcp import fabric_repository_mirror_activation as subject


class Safety:
    def __init__(self):
        self.calls = []

    def assert_action_allowed(self, action):
        self.calls.append(action)


def configure(monkeypatch, tmp_path: Path):
    storage = tmp_path / "runner-data" / "runner-fabric" / "f34"
    inventory = storage / "inventory"
    mirrors = storage / "mirrors"
    inventory.mkdir(parents=True, mode=0o700)
    mirrors.mkdir(mode=0o700)
    for path in (
        tmp_path / "runner-data" / "runner-fabric",
        storage,
        inventory,
        mirrors,
    ):
        os.chmod(path, 0o700)

    config_dir = tmp_path / "config"
    config_dir.mkdir(mode=0o700)
    env_file = config_dir / "runner-mcp.env"
    token = "ghp_" + "x" * 40
    env_file.write_text(
        "RUNNER_MCP_BEARER_TOKEN='existing-secret'\n",
        encoding="utf-8",
    )
    os.chmod(env_file, 0o600)

    monkeypatch.setattr(subject, "_STORAGE_NAMESPACE", storage)
    monkeypatch.setattr(subject, "_INVENTORY_ROOT", inventory)
    monkeypatch.setattr(subject, "_MIRROR_ROOT", mirrors)
    monkeypatch.setattr(
        subject,
        "_ENV_BINDINGS",
        {
            "RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT": inventory,
            "RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT": mirrors,
        },
    )
    return config_dir, token


def test_activation_persists_exact_private_bindings(monkeypatch, tmp_path):
    config_dir, token = configure(monkeypatch, tmp_path)
    environment = {"GITHUB_TOKEN": token}
    safety = Safety()

    result = subject.FabricRepositoryMirrorActivator(
        safety=safety,
        environment=environment,
        config_dir=config_dir,
        github_token=token,
    ).activate()

    assert result == {
        "schemaVersion": "runner-mcp/fabric-repository-mirror-activation/v1",
        "activated": True,
        "storageReady": True,
        "desiredStateBound": True,
        "credentialBindingPresent": True,
        "serviceBindingReady": True,
        "mutationScope": "repository-mirror-activation",
        "reconcileTriggered": False,
    }
    assert token not in json.dumps(result)
    assert len(safety.calls) == 1

    private_dir = config_dir / "repository-mirrors"
    desired = private_dir / "managed-repositories.v1.json"
    git_config = private_dir / "gitconfig"
    assert desired.stat().st_mode & 0o777 == 0o600
    assert git_config.stat().st_mode & 0o777 == 0o600
    payload = json.loads(desired.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == "runner.fabric/managed-repositories/v1"
    assert len(payload["repositories"]) == 11
    assert token not in desired.read_text(encoding="utf-8")
    assert token not in (config_dir / "runner-mcp.env").read_text(encoding="utf-8")

    env_text = (config_dir / "runner-mcp.env").read_text(encoding="utf-8")
    for key in (
        "RUNNER_FABRIC_REPOSITORY_MIRROR_INVENTORY_ROOT",
        "RUNNER_FABRIC_REPOSITORY_MIRROR_ROOT",
        "RUNNER_FABRIC_MANAGED_REPOSITORIES_FILE",
        "RUNNER_FABRIC_REPOSITORY_MIRROR_GIT_CONFIG",
    ):
        assert key in env_text
        assert key in environment


def test_activation_is_idempotent(monkeypatch, tmp_path):
    config_dir, token = configure(monkeypatch, tmp_path)
    environment = {}
    activator = subject.FabricRepositoryMirrorActivator(
        safety=Safety(),
        environment=environment,
        config_dir=config_dir,
        github_token=token,
    )

    first = activator.activate()
    before = (config_dir / "runner-mcp.env").read_bytes()
    second = activator.activate()
    after = (config_dir / "runner-mcp.env").read_bytes()

    assert first["activated"] is True
    assert second["activated"] is True
    assert before == after


def test_activation_requires_existing_github_credential(monkeypatch, tmp_path):
    config_dir, _ = configure(monkeypatch, tmp_path)

    with pytest.raises(
        subject.FabricRepositoryMirrorActivationError,
        match="github-credential-binding-unavailable",
    ):
        subject.FabricRepositoryMirrorActivator(
            safety=Safety(),
            environment={},
            config_dir=config_dir,
            github_token=None,
        ).activate()


def test_activation_rejects_broad_storage_permissions(monkeypatch, tmp_path):
    config_dir, token = configure(monkeypatch, tmp_path)
    os.chmod(subject._MIRROR_ROOT, 0o755)

    with pytest.raises(
        subject.FabricRepositoryMirrorActivationError,
        match="private-directory-unsafe",
    ):
        subject.FabricRepositoryMirrorActivator(
            safety=Safety(),
            environment={},
            config_dir=config_dir,
            github_token=token,
        ).activate()
