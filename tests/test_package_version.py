from importlib.metadata import PackageNotFoundError

from runner_mcp import cli


def test_package_version_uses_canonical_distribution(monkeypatch):
    requested = []

    def fake_version(name: str) -> str:
        requested.append(name)
        return "9.9.9"

    monkeypatch.setattr(cli, "version", fake_version)

    assert cli.package_version() == "9.9.9"
    assert requested == ["aifordable-runner-mcp"]


def test_package_version_falls_back_to_development(monkeypatch):
    def missing(_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(cli, "version", missing)

    assert cli.package_version() == "development"
