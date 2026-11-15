"""Tests voor tools/doc_memory: verliesvrije archivering en lichte groottecontrole.

Doel
    Bewijzen dat ``split`` niets verliest (reconstructie = origineel, byte voor
    byte), dat ``check`` beschadigde archieven als fout meldt, en dat te grote
    bestanden in de standaardmodus alleen een waarschuwing geven, zodat andere
    PR's niet geblokkeerd worden.

Werking
    Elke test bouwt een kleine synthetische repository in ``tmp_path``. De laatste
    test draait ``check`` op de echte repository, zoals de CI dat doet.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "doc_memory" / "doc_memory.py"

_spec = importlib.util.spec_from_file_location("doc_memory", TOOL)
assert _spec and _spec.loader
dm = importlib.util.module_from_spec(_spec)
sys.modules["doc_memory"] = dm  # nodig voor dataclasses
_spec.loader.exec_module(dm)

SAMPLE = (
    "## 2026-11-14 — nieuw werk #101\n\nDetails https://example.com/a en ../docs/x.md\n\n"
    "## 2026-11-02 — ouder werk #77\n\n```\n## geen kop in codeblok\n```\n"
    "sha 0123456789abcdef0123456789abcdef01234567\n\n"
    "## Vaste fase — ongedateerd\n\nDuurzame roadmaptekst.\n\n"
    "## 2026-10-03 — oud #12\n\nOude tekst.\n"
)


def _repo(tmp_path: Path, mode: str = "advisory", target: int = 10) -> tuple[Path, Path]:
    (tmp_path / "handover").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "handover" / "CURRENT_STATE.md").write_text(SAMPLE, encoding="utf-8")
    config = {
        "files": {"handover/CURRENT_STATE.md": {"target_chars": target, "mode": mode}},
        "bootstrap_read_set": ["handover/CURRENT_STATE.md"],
        "duplicate_scan": [],
        "manifest_glob": "**/*.doc-memory.json",
        "infra_scan_globs": ["handover/*.md"],
        "infra_allow_patterns": [],
        "foreign_ref_prefixes": ["Runner-MCP", "AIfordable"],
    }
    cfg = tmp_path / "budget.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")
    return tmp_path, cfg


def _split(root: Path, cfg: Path, *extra: str) -> int:
    return dm.main(
        [
            "--root",
            str(root),
            "--config",
            str(cfg),
            "split",
            "handover/CURRENT_STATE.md",
            "--keep-since",
            "2026-11-10",
            *extra,
        ]
    )


def test_parse_sections_is_exact_and_ignores_code_fences() -> None:
    sections = dm.parse_sections(SAMPLE)
    assert "".join(s.text for s in sections) == SAMPLE
    assert [s.date for s in sections[1:]] == [
        "2026-11-14",
        "2026-11-02",
        None,
        "2026-10-03",
    ]


def test_split_is_lossless_and_keeps_undated_sections(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path)
    original = tmp_path / "original.md"
    original.write_text(SAMPLE, encoding="utf-8")
    assert _split(root, cfg) == 0
    active = (root / "handover" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    assert "nieuw werk" in active and "Vaste fase" in active and "ouder werk" not in active
    assert (root / "handover" / "CURRENT_STATE.archive-2026-11.md").exists()
    assert (root / "handover" / "CURRENT_STATE.archive-2026-10.md").exists()
    manifest = root / "handover" / "CURRENT_STATE.split-2026-11-10.doc-memory.json"
    args = ["--root", str(root), "verify-split", "--manifest", str(manifest)]
    assert dm.main([*args, "--original", str(original)]) == 0


def test_second_split_does_not_duplicate_pointer(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path)
    assert _split(root, cfg) == 0
    assert _split(root, cfg) == 0  # niets meer te archiveren
    active = (root / "handover" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    assert active.count(dm.POINTER_START) == 1


def test_check_detects_modified_archive(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path, target=10**9)
    assert _split(root, cfg) == 0
    archive = root / "handover" / "CURRENT_STATE.archive-2026-10.md"
    archive.write_text(archive.read_text(encoding="utf-8").replace("Oude", "Gewijzigde"))
    assert dm.main(["--root", str(root), "--config", str(cfg), "check"]) == 1


def test_verify_detects_broken_relative_link(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path)
    text = SAMPLE.replace(
        "## 2026-10-03 — oud #12\n", "## 2026-10-03 — oud #12\n[x](../docs/x.md)\n"
    )
    (root / "handover" / "CURRENT_STATE.md").write_text(text, encoding="utf-8")
    original = tmp_path / "original.md"
    original.write_text(text, encoding="utf-8")
    assert _split(root, cfg, "--archive-dir", "handover/archive") == 0
    manifest = root / "handover" / "archive" / "CURRENT_STATE.split-2026-11-10.doc-memory.json"
    args = ["--root", str(root), "verify-split", "--manifest", str(manifest)]
    assert dm.main([*args, "--original", str(original)]) == 1


def test_advisory_budget_never_blocks_but_enforce_does(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path, mode="advisory", target=10)
    assert dm.main(["--root", str(root), "--config", str(cfg), "check"]) == 0
    root2, cfg2 = _repo(tmp_path / "b", mode="enforce", target=10)
    assert dm.main(["--root", str(root2), "--config", str(cfg2), "check"]) == 1


def test_infra_scan_warns_without_failing(tmp_path: Path, capsys) -> None:
    root, cfg = _repo(tmp_path, target=10**9)
    (root / "handover" / "NOTE.md").write_text("host 192.168.1.20\n", encoding="utf-8")
    assert dm.main(["--root", str(root), "--config", str(cfg), "check"]) == 0
    assert "private_ipv4=1" in capsys.readouterr().out


def test_repository_check_passes_in_default_mode() -> None:
    assert dm.main(["--root", str(ROOT), "check"]) == 0


def test_split_refuses_to_archive_infrastructure_data(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path)
    path = root / "handover" / "CURRENT_STATE.md"
    path.write_text(SAMPLE.replace("Oude tekst.", "Oude tekst op 10.1.2.3."), encoding="utf-8")
    assert _split(root, cfg) == 1
    assert not (root / "handover" / "CURRENT_STATE.archive-2026-10.md").exists()


def test_check_fails_on_infrastructure_data_in_archive(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path, target=10**9)
    archive = root / "handover" / "CURRENT_STATE.archive-2026-09.md"
    archive.write_text("## 2026-09-01 — x\n\npad /home/someone/x\n", encoding="utf-8")
    assert dm.main(["--root", str(root), "--config", str(cfg), "check"]) == 1


def test_open_work_stays_visible_and_resplit_is_lossless(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path)
    open_items = tmp_path / "open.json"
    open_items.write_text(
        json.dumps([{"number": 77, "title": "ouder open werk"}, {"number": 101, "title": "x"}]),
        encoding="utf-8",
    )
    assert _split(root, cfg, "--open-items", str(open_items)) == 0
    active_path = root / "handover" / "CURRENT_STATE.md"
    active = active_path.read_text(encoding="utf-8")
    assert "#77 ouder open werk" in active  # alleen in archief besproken, nog open
    assert "- #12 " not in active  # gesloten: niet opgesomd
    # Tweede split met latere datum: blok wordt vervangen, origineel blijft reconstrueerbaar.
    before = tmp_path / "before.md"
    before.write_text(active, encoding="utf-8")
    args = [
        "--root",
        str(root),
        "--config",
        str(cfg),
        "split",
        "handover/CURRENT_STATE.md",
    ]
    assert dm.main([*args, "--keep-since", "2026-11-20", "--open-items", str(open_items)]) == 0
    assert active_path.read_text(encoding="utf-8").count(dm.POINTER_START) == 1
    manifest = root / "handover" / "CURRENT_STATE.split-2026-11-20.doc-memory.json"
    verify = ["--root", str(root), "verify-split", "--manifest", str(manifest)]
    assert dm.main([*verify, "--original", str(before)]) == 0


def test_foreign_repository_references_are_ignored() -> None:
    text = "Runner-MCP #669 en eigen #42 en AIfordable issue #585"
    assert dm.local_issue_refs(text, ["Runner-MCP", "AIfordable"]) == {42}


def test_frozen_copy_must_stay_byte_identical(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path, target=10**9)
    frozen = root / "FULL.md"
    frozen.write_text("origineel\n", encoding="utf-8")
    config = json.loads(cfg.read_text(encoding="utf-8"))
    config["frozen_files"] = {"FULL.md": dm.sha256_text("origineel\n")}
    cfg.write_text(json.dumps(config), encoding="utf-8")
    assert dm.main(["--root", str(root), "--config", str(cfg), "check"]) == 0
    frozen.write_text("gewijzigd\n", encoding="utf-8")
    assert dm.main(["--root", str(root), "--config", str(cfg), "check"]) == 1


def test_insert_and_archive_undated_stay_lossless(tmp_path: Path) -> None:
    root, cfg = _repo(tmp_path)
    original = tmp_path / "original.md"
    original.write_text(SAMPLE, encoding="utf-8")
    lanes = tmp_path / "lanes.md"
    lanes.write_text("## Actuele toestand per lane\n\n- A7: WAIT\n", encoding="utf-8")
    assert _split(root, cfg, "--insert", str(lanes), "--archive-undated", "^## Vaste fase") == 0
    active = (root / "handover" / "CURRENT_STATE.md").read_text(encoding="utf-8")
    assert "Actuele toestand per lane" in active and "Vaste fase" not in active
    assert (root / "handover" / "CURRENT_STATE.archive-undated.md").exists()
    manifest = root / "handover" / "CURRENT_STATE.split-2026-11-10.doc-memory.json"
    args = ["--root", str(root), "verify-split", "--manifest", str(manifest)]
    assert dm.main([*args, "--original", str(original)]) == 0
