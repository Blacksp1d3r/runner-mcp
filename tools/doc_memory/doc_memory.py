#!/usr/bin/env python3
"""Doc-memory: omvang, verliesvrije archivering en controle van projectgeheugen.

Doel
    De bestaande Markdown-bestanden (AGENTS.md, CURRENT_STATE, SESSION_HANDOFF,
    ROADMAP, ...) blijven het duurzame projectgeheugen. Dit script helpt ze klein
    en actueel te houden zonder informatie te verliezen. Het voegt GEEN nieuw
    geheugen-, taak- of beslissingssysteem toe: het meet, verplaatst oude secties
    byte-voor-byte naar archiefbestanden en controleert dat er niets verloren gaat.

Werking (subcommando's)
    measure       Meet omvang per bestand en de context die een agent bij de
                  verplichte opstart moet lezen (bootstrap-leesset).
    check         Lichte CI-controle: groottegrenzen (standaard alleen
                  waarschuwing), integriteit van bestaande archieven en
                  bevroren kopieën, en vertrouwelijke infrastructuurdata
                  (waarschuwing in actieve bestanden, fout in archieven).
    split         Verplaatst gedateerde secties ouder dan een datum ongewijzigd
                  naar maandarchieven en schrijft een manifest met hashes.
    verify-split  Reconstrueert het originele bestand uit actief bestand +
                  archieven en vergelijkt de SHA-256 met het origineel.

Aanroepers / afhankelijkheden
    Alleen de Python-standaardbibliotheek (3.12+). Wordt aangeroepen vanuit de
    bestaande CI en handmatig tijdens een migratie. Configuratie staat in
    ``budget.json`` naast dit script.

Invoer / uitvoer
    Leest Markdown uit de repository; ``split`` schrijft actieve bestanden,
    archieven en een JSON-manifest. Het script voert geen netwerk-, host- of
    GitHub-acties uit.

Risico's
    ``split`` herschrijft het actieve bestand. Gebruik het alleen op een aparte
    branch, gevolgd door ``verify-split``. Sectiegrenzen zijn regels die met
    ``## `` beginnen buiten codeblokken; inhoud wordt nooit herschreven.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR / "budget.json"
MANIFEST_SCHEMA = "doc-memory-split/v1"

# Vaste tekst die bovenaan een actief bestand wordt gezet na de eerste split.
# Ze verandert nooit, zodat een volgende split het actieve bestand niet hoeft
# te herschrijven buiten het verplaatsen van secties.
POINTER_START = "<!-- doc-memory:archive-pointer -->"
POINTER_END = "<!-- /doc-memory:archive-pointer -->"

ISO_DATE = re.compile(r"\b(20\d\d-[01]\d-[0-3]\d)\b")
FENCE = re.compile(r"^\s*(```|~~~)")

# Verwijzingen die na een archivering terug te vinden moeten zijn.
REFERENCE_PATTERNS = {
    "issue_or_pr": re.compile(r"(?<![\w/])#\d{2,6}\b"),
    "url": re.compile(r"https?://[^\s)>\]]+"),
    "sha40": re.compile(r"\b[0-9a-f]{40}\b"),
    "relative_link": re.compile(r"\]\((?!https?://|#|mailto:)([^)\s#]+)(#[^)\s]*)?\)"),
}

# Mogelijke vertrouwelijke infrastructuurgegevens. Alleen waarschuwingen:
# de projectregels verbieden zulke gegevens in Git; dit helpt ze opmerken.
INFRA_PATTERNS = {
    "private_ipv4": re.compile(
        r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"
    ),
    "home_path": re.compile(
        r"(?<![\w/.-])(?:/home/|/Users/)[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\[A-Za-z0-9._-]+"
    ),
    "lan_hostname": re.compile(r"\b[a-z0-9-]+\.(?:lan|local|internal|home\.arpa)\b", re.IGNORECASE),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "windows_hostname": re.compile(r"\bDESKTOP-[A-Z0-9]{5,}\b"),
}


@dataclass
class Section:
    """Eén stuk van een Markdown-bestand: de preambule of een ``## ``-sectie.

    ``text`` is exact de oorspronkelijke tekst inclusief kopregel en
    regeleinden; de concatenatie van alle secties geeft het bestand terug.
    """

    index: int
    heading: str
    text: str
    date: str | None

    @property
    def sha256(self) -> str:
        return sha256_text(self.text)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(chars: int) -> int:
    """Ruwe schatting: ~4 tekens per token. Genoeg om grootteordes te vergelijken."""
    return round(chars / 4)


def parse_sections(text: str) -> list[Section]:
    """Splits tekst op ``## ``-kopregels buiten codeblokken.

    Sectie 0 is de preambule (mag leeg zijn). De datum is de eerste ISO-datum
    (JJJJ-MM-DD) in de kopregel, of ``None`` voor ongedateerde secties zoals
    vaste roadmapfasen. Ongedateerde secties worden nooit gearchiveerd.
    """
    lines = text.splitlines(keepends=True)
    sections: list[Section] = []
    current: list[str] = []
    heading = ""
    in_fence = False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            sections.append(_make_section(len(sections), heading, current))
            current = [line]
            heading = line.rstrip("\n")
            continue
        current.append(line)
    sections.append(_make_section(len(sections), heading, current))
    return sections


def _make_section(index: int, heading: str, lines: list[str]) -> Section:
    match = ISO_DATE.search(heading) if heading else None
    return Section(index, heading, "".join(lines), match.group(1) if match else None)


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def file_stats(path: Path) -> dict:
    """Meet één bestand: grootte, secties, datumbereik en geschatte tokens."""
    if not path.exists():
        return {"exists": False}
    text = read_text(path)
    sections = parse_sections(text)
    dates = sorted(s.date for s in sections if s.date)
    return {
        "exists": True,
        "bytes": len(text.encode("utf-8")),
        "chars": len(text),
        "lines": text.count("\n"),
        "sections": len(sections) - 1,
        "dated_sections": len(dates),
        "oldest_date": dates[0] if dates else None,
        "newest_date": dates[-1] if dates else None,
        "est_tokens": estimate_tokens(len(text)),
    }


def duplicate_sections(root: Path, paths: list[str]) -> dict:
    """Vindt secties die letterlijk in meer dan één bestand voorkomen.

    Dezelfde dagboeksectie in CURRENT_STATE, SESSION_HANDOFF en ROADMAP kost
    driemaal context. Geeft het aantal gedeelde secties en de dubbele tekens.
    """
    seen: dict[str, list[tuple[str, int]]] = {}
    for rel in paths:
        path = root / rel
        if not path.exists():
            continue
        for section in parse_sections(read_text(path))[1:]:
            body = section.text.strip()
            if len(body) < 200:
                continue
            seen.setdefault(sha256_text(body), []).append((rel, len(section.text)))
    shared = {digest: hits for digest, hits in seen.items() if len(hits) > 1}
    duplicated_chars = sum(sum(size for _, size in hits[1:]) for hits in shared.values())
    return {"shared_sections": len(shared), "duplicated_chars": duplicated_chars}


def command_measure(args: argparse.Namespace) -> int:
    """Druk een meting af (tekst of JSON) van budgetbestanden en bootstrap-leesset."""
    root = Path(args.root).resolve()
    config = load_config(Path(args.config))
    files = {rel: file_stats(root / rel) for rel in config["files"]}
    bootstrap = {rel: file_stats(root / rel) for rel in config.get("bootstrap_read_set", [])}
    boot_chars = sum(s.get("chars", 0) for s in bootstrap.values())
    report = {
        "root": str(root),
        "files": files,
        "bootstrap_read_set": bootstrap,
        "bootstrap_total_chars": boot_chars,
        "bootstrap_est_tokens": estimate_tokens(boot_chars),
        "duplicates": duplicate_sections(root, list(config.get("duplicate_scan", []))),
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    print(f"{'bestand':<42} {'tekens':>10} {'doel':>8} {'secties':>8} {'~tokens':>9}")
    for rel, stats in files.items():
        if not stats["exists"]:
            print(f"{rel:<42} {'(ontbreekt)':>10}")
            continue
        target = config["files"][rel]["target_chars"]
        print(
            f"{rel:<42} {stats['chars']:>10,} {target:>8,} "
            f"{stats['sections']:>8} {stats['est_tokens']:>9,}"
        )
    print(f"\nBootstrap-leesset: {boot_chars:,} tekens ≈ {estimate_tokens(boot_chars):,} tokens")
    dup = report["duplicates"]
    print(
        f"Letterlijk gedeelde secties: {dup['shared_sections']} "
        f"({dup['duplicated_chars']:,} dubbele tekens)"
    )
    return 0


def git_show(rev: str, rel: str) -> str | None:
    """Lees een bestand op een git-revisie; ``None`` als het daar niet bestaat."""
    proc = subprocess.run(["git", "show", f"{rev}:{rel}"], capture_output=True, check=False)
    if proc.returncode:
        return None
    return proc.stdout.decode("utf-8")


def check_budgets(root: Path, config: dict, base: str | None) -> tuple[list[str], list[str]]:
    """Vergelijk bestandsgroottes met de streefwaarden.

    Modi per bestand:
      advisory   alleen waarschuwen (standaard; blokkeert geen andere PR's);
      no_growth  fout als het bestand t.o.v. ``--base`` groter werd terwijl het
                 al boven het doel zat (overgangsfase na migratie);
      enforce    fout zodra het bestand boven het doel zit.
    Geeft (waarschuwingen, fouten) terug.
    """
    warnings: list[str] = []
    errors: list[str] = []
    for rel, rule in config["files"].items():
        path = root / rel
        if not path.exists():
            continue
        size = len(read_text(path))
        target = int(rule["target_chars"])
        mode = rule.get("mode", "advisory")
        if size <= target:
            continue
        message = f"{rel}: {size:,} tekens, streefwaarde {target:,} (modus {mode})"
        if mode == "enforce":
            errors.append(message)
        elif mode == "no_growth" and base:
            previous = git_show(base, rel)
            if previous is not None and size > len(previous):
                errors.append(f"{message}; groeide van {len(previous):,} t.o.v. basis")
            else:
                warnings.append(message)
        else:
            warnings.append(message)
    return warnings, errors


def check_archives(root: Path, config: dict) -> list[str]:
    """Controleer dat gearchiveerde secties uit elk manifest nog ongewijzigd bestaan.

    Archieven zijn alleen-aanvullen: een gearchiveerde sectie mag niet worden
    gewijzigd of verwijderd. Elke afwijking is een fout (historisch bewijs).
    """
    errors: list[str] = []
    for manifest_path in sorted(root.glob(config.get("manifest_glob", "**/*.doc-memory.json"))):
        manifest = json.loads(read_text(manifest_path))
        if manifest.get("schema") != MANIFEST_SCHEMA:
            errors.append(f"{manifest_path}: onbekend manifestschema")
            continue
        cache: dict[str, str] = {}
        for entry in manifest["sections"]:
            dest = entry["dest"]
            if dest == manifest["active_path"]:
                continue
            if dest not in cache:
                dest_path = root / dest
                cache[dest] = read_text(dest_path) if dest_path.exists() else ""
            if not _contains_section(cache[dest], entry):
                errors.append(
                    f"{dest}: gearchiveerde sectie {entry['index']} ({entry['heading'][:60]!r}) "
                    "ontbreekt of is gewijzigd"
                )
    return errors


def _contains_section(haystack: str, entry: dict) -> bool:
    """Zoek een sectie op zijn exacte tekst; bevestig met lengte en SHA-256."""
    start = 0
    while True:
        pos = haystack.find(entry["first_line"], start)
        if pos < 0:
            return False
        candidate = haystack[pos : pos + entry["chars"]]
        if sha256_text(candidate) == entry["sha256"]:
            return True
        start = pos + 1


def infra_counts(text: str, allow: list[re.Pattern[str]]) -> dict[str, int]:
    """Tel per patroon de mogelijke vertrouwelijke infrastructuurwaarden in tekst."""
    counts: dict[str, int] = {}
    for line in text.splitlines():
        for name, regex in INFRA_PATTERNS.items():
            for match in regex.finditer(line):
                if any(a.search(match.group(0)) for a in allow):
                    continue
                counts[name] = counts.get(name, 0) + 1
    return counts


def scan_infra(root: Path, config: dict) -> tuple[list[str], list[str]]:
    """Zoek patronen die op vertrouwelijke infrastructuurgegevens lijken.

    In actieve bestanden is een treffer een waarschuwing. In archiefbestanden
    (``*.archive-*.md``) is het een fout: archieven mogen nooit vertrouwelijke
    gegevens byte-identiek bewaren. Geeft (waarschuwingen, fouten) terug.
    """
    warnings: list[str] = []
    errors: list[str] = []
    patterns = list(config.get("infra_scan_globs", []))
    patterns.append(config.get("archive_glob", "**/*.archive-*.md"))
    allow = [re.compile(p) for p in config.get("infra_allow_patterns", [])]
    paths = sorted({p for pattern in patterns for p in root.glob(pattern) if p.is_file()})
    for path in paths:
        counts = infra_counts(read_text(path), allow)
        if not counts:
            continue
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        message = f"{path.relative_to(root)}: mogelijke infrastructuurdata ({summary})"
        (errors if ".archive-" in path.name else warnings).append(message)
    return warnings, errors


def check_frozen(root: Path, config: dict) -> list[str]:
    """Controleer dat bevroren kopieën (bv. de volledige oude AGENTS.md) byte-identiek blijven."""
    errors: list[str] = []
    for rel, expected in config.get("frozen_files", {}).items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: bevroren bestand ontbreekt")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"{rel}: bevroren bestand is gewijzigd (SHA-256 wijkt af)")
    return errors


def command_check(args: argparse.Namespace) -> int:
    """CI-controle. Exitcode 1 alleen bij afgedwongen grenzen of archiefschade."""
    root = Path(args.root).resolve()
    config = load_config(Path(args.config))
    warnings, errors = check_budgets(root, config, args.base)
    errors += check_archives(root, config)
    errors += check_frozen(root, config)
    infra_warnings, infra_errors = scan_infra(root, config)
    warnings += infra_warnings
    errors += infra_errors
    annotate = args.github
    for message in warnings:
        print(f"::warning title=doc-memory::{message}" if annotate else f"WAARSCHUWING {message}")
    for message in errors:
        print(f"::error title=doc-memory::{message}" if annotate else f"FOUT {message}")
    print(f"doc-memory check: {len(warnings)} waarschuwing(en), {len(errors)} fout(en)")
    return 1 if errors else 0


def first_line(text: str) -> str:
    return text.splitlines(keepends=True)[0] if text else ""


ISSUE_REF = re.compile(r"(?<![\w/])#(\d{2,6})\b")


def local_issue_refs(text: str, foreign_prefixes: list[str]) -> set[int]:
    """Issue-/PR-nummers van deze repository in tekst.

    Verwijzingen als ``Runner-MCP #669`` horen bij een andere repository en
    worden overgeslagen (prefixen uit ``foreign_ref_prefixes`` in budget.json).
    """
    refs: set[int] = set()
    for match in ISSUE_REF.finditer(text):
        before = text[max(0, match.start() - 30) : match.start()].rstrip()
        before = re.sub(r"(?i)(issue|pr|pull request)$", "", before).rstrip()
        if any(before.endswith(prefix) for prefix in foreign_prefixes):
            continue
        refs.add(int(match.group(1)))
    return refs


def strip_generated(text: str) -> tuple[str, str, int]:
    """Haal een eerder gegenereerd verwijzingsblok weg (het wordt telkens opnieuw gemaakt).

    Geeft (tekst zonder blok, verwijderd blok, positie) terug; positie -1 als er
    geen blok was. Het manifest bewaart het verwijderde blok, zodat het
    origineel nog altijd exact te reconstrueren is.
    """
    start = text.find(POINTER_START)
    if start < 0:
        return text, "", -1
    end = text.find(POINTER_END, start)
    if end < 0:
        return text, "", -1
    end += len(POINTER_END)
    while end < len(text) and text[end] == "\n":
        end += 1
    return text[:start] + text[end:], text[start:end], start


def generated_block(archive_hint: str, open_lines: list[str]) -> str:
    """Bouw het vaste verwijzingsblok bovenaan het actieve bestand.

    Het blok verwijst naar de archieven en somt open issues/PR's op die alleen
    nog in gearchiveerde secties besproken worden, zodat actieve taken,
    blokkades en afhankelijkheden zichtbaar blijven ongeacht hun ouderdom.
    """
    lines = [
        POINTER_START,
        (
            "> **Actief bestand.** Oudere gedateerde secties staan ongewijzigd in "
            f"`{archive_hint}` (manifest met SHA-256 per sectie ernaast). Lees die niet "
            'standaard; zoek gericht, bv. `grep -n "#1234"`.'
        ),
    ]
    if open_lines:
        lines += [
            ">",
            (
                "> **Nog open werk waarvan de historie in het archief staat** "
                "(open issue/PR op het moment van archiveren; status volgt GitHub):"
            ),
            *[f"> {line}" for line in open_lines],
        ]
    lines.append(POINTER_END)
    return "\n".join(lines) + "\n\n"


def command_split(args: argparse.Namespace) -> int:
    """Verplaats gedateerde secties ouder dan ``--keep-since`` naar maandarchieven.

    Werkwijze: secties worden niet herschreven, alleen verplaatst. Het actieve
    bestand behoudt preambule, ongedateerde secties en recente secties in de
    oorspronkelijke volgorde. Archieven per maand houden ook de oorspronkelijke
    volgorde; nieuwere secties komen bovenaan een bestaand archief (nieuwste
    eerst, zoals de bronbestanden). Het manifest registreert per sectie de
    SHA-256 en bestemming, zodat ``verify-split`` en ``check`` alles kunnen
    nagaan.
    """
    root = Path(args.root).resolve()
    rel = args.file
    source_path = root / rel
    original = read_text(source_path)
    base, removed_generated, removed_offset = strip_generated(original)
    sections = parse_sections(base)
    config = load_config(Path(args.config))
    foreign = list(config.get("foreign_ref_prefixes", []))
    archive_dir = Path(args.archive_dir) if args.archive_dir else Path(rel).parent
    stem = Path(rel).stem

    archive_undated = re.compile(args.archive_undated) if args.archive_undated else None

    def archive_rel(date: str | None) -> str:
        period = date[:7] if date else "undated"
        return (archive_dir / f"{stem}.archive-{period}.md").as_posix()

    keep: list[Section] = []
    moved: dict[str, list[Section]] = {}
    entries = []
    for section in sections:
        is_old = section.index > 0 and (
            (section.date is not None and section.date < args.keep_since)
            or (
                section.date is None
                and archive_undated is not None
                and archive_undated.search(section.heading) is not None
            )
        )
        dest = archive_rel(section.date) if is_old else rel
        (moved.setdefault(dest, []) if is_old else keep).append(section)
        entries.append(
            {
                "index": section.index,
                "heading": section.heading,
                "date": section.date,
                "chars": len(section.text),
                "sha256": section.sha256,
                "first_line": first_line(section.text),
                "dest": dest,
            }
        )
    if not moved:
        print("Niets te archiveren voor deze datum.")
        return 0

    open_lines = _open_work_lines(args, keep, moved, foreign)
    hint = (archive_dir / f"{stem}.archive-*.md").as_posix()
    block = generated_block(hint, open_lines)
    inserted = read_text(Path(args.insert)) if args.insert else ""
    if inserted and not inserted.endswith("\n\n"):
        inserted = inserted.rstrip("\n") + "\n\n"
    active_text = keep[0].text + block + inserted + "".join(s.text for s in keep[1:])
    allow = [re.compile(p) for p in config.get("infra_allow_patterns", [])]
    leaks = [
        s.heading[:60] for items in moved.values() for s in items if infra_counts(s.text, allow)
    ]
    if leaks:
        print(
            f"FOUT: {len(leaks)} te archiveren sectie(s) bevatten infrastructuurdata; eerst redigeren:"
        )
        for heading in leaks[:10]:
            print(f"  {heading}")
        return 1

    outputs: dict[str, str] = {rel: active_text}
    for dest, items in moved.items():
        dest_path = root / dest
        existing = read_text(dest_path) if dest_path.exists() else ""
        outputs[dest] = "".join(s.text for s in items) + existing

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "source_path": rel,
        "active_path": rel,
        "source_sha256": sha256_text(original),
        "source_chars": len(original),
        "base_sha256": sha256_text(base),
        "removed_generated": removed_generated,
        "removed_offset": removed_offset,
        "open_work_listed": len(open_lines),
        "inserted_sha256": sha256_text(inserted) if inserted else None,
        "keep_since": args.keep_since,
        "sections": entries,
        "outputs": {path: sha256_text(text) for path, text in outputs.items()},
    }
    manifest_rel = (archive_dir / f"{stem}.split-{args.keep_since}.doc-memory.json").as_posix()
    print(f"Actief: {rel} {len(original):,} -> {len(active_text):,} tekens")
    for dest, items in moved.items():
        print(f"Archief: {dest} (+{len(items)} secties)")
    print(f"Manifest: {manifest_rel}")
    print(f"Open werk uit archief zichtbaar gehouden: {len(open_lines)}")
    if args.dry_run:
        print("(dry-run: niets geschreven)")
        return 0
    for path, text in outputs.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (root / manifest_rel).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


def _open_work_lines(
    args: argparse.Namespace,
    keep: list[Section],
    moved: dict[str, list[Section]],
    foreign: list[str],
) -> list[str]:
    """Lijst open issues/PR's die alleen nog in te archiveren secties voorkomen."""
    if not args.open_items:
        return []
    open_items = {
        int(item["number"]): str(item.get("title", "")).replace("\n", " ")[:100]
        for item in json.loads(read_text(Path(args.open_items)))
    }
    kept_refs: set[int] = set()
    for section in keep:
        kept_refs |= local_issue_refs(section.text, foreign)
    archived: dict[int, tuple[str, str]] = {}
    sources = [(dest, section) for dest, items in moved.items() for section in items]
    root = Path(args.root).resolve()
    for pattern in args.open_scan or []:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            sources += [(rel, s) for s in parse_sections(read_text(path))[1:]]
    for dest, section in sources:
        for number in local_issue_refs(section.text, foreign):
            previous = archived.get(number)
            if previous is None or (section.date or "") > previous[1]:
                archived[number] = (dest, section.date or "")
    lines = []
    for number in sorted(set(archived) - kept_refs, reverse=True):
        if number in open_items:
            dest, date = archived[number]
            lines.append(f"- #{number} {open_items[number]} — laatst {date} in `{dest}`")
    return lines


def collect_references(text: str) -> dict[str, set[str]]:
    return {name: set(rx.findall(text)) for name, rx in REFERENCE_PATTERNS.items()}


def github_slug(heading: str) -> str:
    """Benader de GitHub-ankernaam van een kopregel (voor inkomende links)."""
    title = heading.lstrip("#").strip().lower()
    title = re.sub(r"[^\w\- ]", "", title)
    return title.replace(" ", "-")


def command_verify_split(args: argparse.Namespace) -> int:
    """Bewijs dat een split verliesvrij is.

    Controles:
      1. SHA-256 van het origineel komt overeen met het manifest;
      2. elke sectie staat byte-identiek in haar bestemming;
      3. alle secties samen in volgorde geven exact het origineel terug;
      4. alle verwijzingen (issues/PR's, URL's, SHA's, links) blijven aanwezig;
      5. relatieve links in verplaatste secties werken vanaf de nieuwe plek;
      6. inkomende ``bestand#anker``-links naar verplaatste koppen worden gemeld.
    """
    root = Path(args.root).resolve()
    manifest = json.loads(read_text(Path(args.manifest)))
    if args.original.startswith("git:"):
        rev, _, rel = args.original[4:].partition(":")
        original = git_show(rev, rel)
        if original is None:
            print(f"FOUT origineel niet gevonden: {args.original}")
            return 1
    else:
        original = read_text(Path(args.original))
    errors: list[str] = []
    warnings: list[str] = []
    if sha256_text(original) != manifest["source_sha256"]:
        errors.append("SHA-256 van het origineel wijkt af van het manifest")

    texts: dict[str, str] = {}
    rebuilt_parts: list[str] = []
    for entry in manifest["sections"]:
        dest = entry["dest"]
        if dest not in texts:
            texts[dest] = read_text(root / dest) if (root / dest).exists() else ""
        haystack = texts[dest]
        found = None
        start = 0
        while found is None:
            pos = haystack.find(entry["first_line"], start) if entry["first_line"] else 0
            if pos < 0:
                break
            candidate = haystack[pos : pos + entry["chars"]]
            if sha256_text(candidate) == entry["sha256"]:
                found = candidate
            start = pos + 1
            if not entry["first_line"]:
                break
        if found is None:
            errors.append(f"sectie {entry['index']} niet byte-identiek gevonden in {dest}")
            continue
        rebuilt_parts.append(found)
    rebuilt = "".join(rebuilt_parts)
    expected = manifest.get("base_sha256", manifest["source_sha256"])
    offset = manifest.get("removed_offset", -1)
    if offset >= 0:
        rebuilt_full = rebuilt[:offset] + manifest["removed_generated"] + rebuilt[offset:]
    else:
        rebuilt_full = rebuilt
    if sha256_text(rebuilt) != expected or sha256_text(rebuilt_full) != manifest["source_sha256"]:
        errors.append("reconstructie uit actief bestand + archieven is niet gelijk aan origineel")

    union = "".join(texts.values())
    # Het gegenereerde verwijzingsblok is afgeleide data (in het manifest bewaard);
    # alleen echte inhoud moet zijn verwijzingen behouden.
    before = collect_references(original.replace(manifest.get("removed_generated", ""), "", 1))
    after = collect_references(union)
    for name, refs in before.items():
        missing = refs - after[name]
        if missing:
            errors.append(f"{len(missing)} verwijzing(en) van type {name} verdwenen")

    source_dir = (root / manifest["source_path"]).parent
    moved_entries = [e for e in manifest["sections"] if e["dest"] != manifest["active_path"]]
    for entry in moved_entries:
        text = texts.get(entry["dest"], "")
        pos = text.find(entry["first_line"])
        body = text[pos : pos + entry["chars"]] if pos >= 0 else ""
        dest_dir = (root / entry["dest"]).parent
        for link, _anchor in REFERENCE_PATTERNS["relative_link"].findall(body):
            if (source_dir / link).exists() and not (dest_dir / link).exists():
                errors.append(f"relatieve link {link!r} breekt in {entry['dest']}")

    moved_slugs = {github_slug(e["heading"]) for e in moved_entries}
    source_name = Path(manifest["source_path"]).name
    inbound = 0
    for md in root.rglob("*.md"):
        if ".git" in md.parts:
            continue
        for match in re.finditer(
            rf"{re.escape(source_name)}#([\w\-]+)",
            md.read_text(encoding="utf-8", errors="ignore"),
        ):
            if match.group(1) in moved_slugs:
                inbound += 1
    if inbound:
        warnings.append(f"{inbound} inkomende ankerlink(s) wijzen naar nu gearchiveerde koppen")

    for message in warnings:
        print(f"WAARSCHUWING {message}")
    for message in errors:
        print(f"FOUT {message}")
    status = "VERLIESVRIJ" if not errors else "NIET VERLIESVRIJ"
    print(
        f"{status}: {len(manifest['sections'])} secties, {len(moved_entries)} gearchiveerd, "
        f"origineel sha256={manifest['source_sha256'][:12]}…"
    )
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository-root (standaard: .)")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="pad naar budget.json")
    sub = parser.add_subparsers(dest="command", required=True)

    measure = sub.add_parser("measure", help="meet omvang en bootstrap-context")
    measure.add_argument("--json", action="store_true")
    measure.set_defaults(func=command_measure)

    check = sub.add_parser("check", help="lichte CI-controle")
    check.add_argument("--base", help="git-revisie voor no_growth-vergelijking")
    check.add_argument("--github", action="store_true", help="GitHub-annotaties")
    check.set_defaults(func=command_check)

    split = sub.add_parser("split", help="archiveer oude gedateerde secties")
    split.add_argument("file", help="pad t.o.v. root, bv. handover/CURRENT_STATE.md")
    split.add_argument("--keep-since", required=True, help="JJJJ-MM-DD; ouder gaat naar archief")
    split.add_argument("--archive-dir", help="map voor archieven (standaard: map van het bestand)")
    split.add_argument("--dry-run", action="store_true")
    split.add_argument(
        "--archive-undated",
        help="regex: ongedateerde secties met overeenkomende kop ook archiveren",
    )
    split.add_argument(
        "--insert",
        help="bestand met nieuwe (geconsolideerde) tekst, ingevoegd na het verwijzingsblok",
    )
    split.add_argument(
        "--open-scan",
        action="append",
        help="glob van bestaande archieven waarvan open verwijzingen ook vermeld worden",
    )
    split.add_argument(
        "--open-items",
        help="JSON-lijst [{number, title}] van open issues/PR's (export uit GitHub)",
    )
    split.set_defaults(func=command_split)

    verify = sub.add_parser("verify-split", help="bewijs dat een split verliesvrij is")
    verify.add_argument("--manifest", required=True)
    verify.add_argument(
        "--original",
        required=True,
        help="pad naar origineel of git:REV:pad/naar/bestand",
    )
    verify.set_defaults(func=command_verify_split)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "keep_since", None) and not ISO_DATE.fullmatch(args.keep_since):
        print("--keep-since moet JJJJ-MM-DD zijn")
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
