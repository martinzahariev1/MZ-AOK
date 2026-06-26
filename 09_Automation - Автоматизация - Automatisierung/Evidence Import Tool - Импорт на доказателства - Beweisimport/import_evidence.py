#!/usr/bin/env python3
"""Register evidence files without parsing or modifying their contents."""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import mimetypes
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = REPO_ROOT / "00_Case Dashboard - Табло на случая - Fallübersicht"
DOCUMENTS_CSV = DASHBOARD_DIR / "documents.csv"
EVIDENCE_ROOT = REPO_ROOT / "02_Evidence - Доказателства - Beweismittel"
LOG_PATH = Path(__file__).resolve().parent / "import_log.csv"

DOCUMENTS_HEADERS = [
    "document_id",
    "date",
    "folder",
    "filename",
    "document_type",
    "source",
    "language",
    "status",
    "related_person",
    "related_company",
    "summary",
    "notes",
]

LOG_HEADERS = [
    "timestamp_utc",
    "evidence_id",
    "source_path",
    "destination_path",
    "metadata_path",
    "detected_type",
    "sha256_hash",
    "result",
]


@dataclass(frozen=True)
class TypeInfo:
    prefix: str
    document_type: str
    folder_name: str
    mime_type: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register evidence files, copy originals, create JSON metadata, and update documents.csv."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more file paths, directory paths, or glob patterns to import.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    return datetime.now().date().isoformat()


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def expand_inputs(raw_paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in raw_paths:
        matches = [Path(match) for match in glob.glob(raw_path)] if any(ch in raw_path for ch in "*?[]") else []
        candidates = matches or [Path(raw_path)]
        for candidate in candidates:
            candidate = candidate.expanduser()
            if candidate.is_dir():
                files.extend(path for path in candidate.rglob("*") if path.is_file())
            elif candidate.is_file():
                files.append(candidate)
            else:
                raise FileNotFoundError(f"Input path not found: {raw_path}")

    unique_files: list[Path] = []
    seen: set[Path] = set()
    for file_path in files:
        resolved = file_path.resolve()
        if resolved not in seen:
            unique_files.append(resolved)
            seen.add(resolved)
    return unique_files


def detect_file_type(file_path: Path) -> TypeInfo:
    suffix = file_path.suffix.lower()
    name = file_path.name.lower()
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    if suffix in {".eml", ".msg"}:
        return TypeInfo("MAIL", "Email", "Emails - Имейли - E-Mails", mime_type)
    if "whatsapp" in name or "chat" in name or suffix in {".wa", ".chat"}:
        return TypeInfo("CHAT", "Chat", "Chats - Чатове - Chats", mime_type)
    if "court" in name or "gericht" in name or "съд" in name:
        return TypeInfo("COURT", "Court Document", "Court - Съд - Gericht", mime_type)
    if "police" in name or "polizei" in name or "полиция" in name:
        return TypeInfo("POLICE", "Police Document", "Police - Полиция - Polizei", mime_type)
    if "bank" in name or "statement" in name or "konto" in name:
        return TypeInfo("BANK", "Bank Record", "Bank - Банка - Bank", mime_type)
    if "payment" in name or "pay-" in name or "zahlung" in name or "плащане" in name:
        return TypeInfo("PAY", "Payment Record", "Payments - Плащания - Zahlungen", mime_type)
    if mime_type.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}:
        return TypeInfo("PHOTO", "Photo or Image", "Photos - Снимки - Fotos", mime_type)

    return TypeInfo("DOC", "Document", "Documents - Документи - Dokumente", mime_type)


def read_existing_ids() -> dict[str, int]:
    max_ids: dict[str, int] = {}
    pattern = re.compile(r"\b([A-Z]+)-(\d{6})\b")

    if DOCUMENTS_CSV.exists():
        with DOCUMENTS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                for value in row.values():
                    if not value:
                        continue
                    for match in pattern.finditer(value):
                        prefix, number = match.groups()
                        max_ids[prefix] = max(max_ids.get(prefix, 0), int(number))

    for metadata_path in EVIDENCE_ROOT.rglob("*.metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        evidence_id = str(metadata.get("evidence_id", ""))
        match = pattern.search(evidence_id)
        if match:
            prefix, number = match.groups()
            max_ids[prefix] = max(max_ids.get(prefix, 0), int(number))

    return max_ids


def next_evidence_id(type_info: TypeInfo, max_ids: dict[str, int]) -> str:
    next_number = max_ids.get(type_info.prefix, 0) + 1
    max_ids[type_info.prefix] = next_number
    return f"{type_info.prefix}-{next_number:06d}"


def safe_filename(filename: str) -> str:
    path = Path(filename)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-._") or "evidence"
    suffix = re.sub(r"[^A-Za-z0-9.]+", "", path.suffix)
    return f"{stem[:120]}{suffix}"


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_csv(path: Path, headers: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)


def append_csv_row(path: Path, headers: list[str], row: dict[str, str]) -> None:
    ensure_csv(path, headers)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writerow(row)


def copy_without_overwrite(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def import_file(source_path: Path, max_ids: dict[str, int]) -> dict[str, str]:
    type_info = detect_file_type(source_path)
    evidence_id = next_evidence_id(type_info, max_ids)
    destination_dir = EVIDENCE_ROOT / type_info.folder_name
    destination_name = f"{evidence_id}_{safe_filename(source_path.name)}"
    destination_path = destination_dir / destination_name
    metadata_path = destination_path.with_name(f"{destination_path.name}.metadata.json")

    if metadata_path.exists():
        raise FileExistsError(f"Metadata already exists: {metadata_path}")

    copy_without_overwrite(source_path, destination_path)
    file_hash = sha256_file(destination_path)

    metadata = {
        "evidence_id": evidence_id,
        "classification": "Original Evidence",
        "confidence": "Unverified",
        "date": today(),
        "source": "",
        "language": "",
        "original_filename": source_path.name,
        "current_filename": destination_path.name,
        "file_location": repo_relative(destination_path),
        "detected_file_type": type_info.document_type,
        "mime_type": type_info.mime_type,
        "file_size_bytes": destination_path.stat().st_size,
        "sha256_hash": file_hash,
        "summary": "",
        "related_people": [],
        "related_companies": [],
        "related_events": [],
        "related_evidence": [],
        "keywords": [],
        "confidence_notes": "",
        "notes": "",
        "import": {
            "timestamp_utc": utc_now(),
            "source_path": str(source_path),
            "tool": "import_evidence.py",
        },
    }

    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_csv_row(
        DOCUMENTS_CSV,
        DOCUMENTS_HEADERS,
        {
            "document_id": evidence_id,
            "date": metadata["date"],
            "folder": repo_relative(destination_dir),
            "filename": destination_path.name,
            "document_type": type_info.document_type,
            "source": "",
            "language": "",
            "status": "original",
            "related_person": "",
            "related_company": "",
            "summary": "",
            "notes": "",
        },
    )

    log_row = {
        "timestamp_utc": metadata["import"]["timestamp_utc"],
        "evidence_id": evidence_id,
        "source_path": str(source_path),
        "destination_path": repo_relative(destination_path),
        "metadata_path": repo_relative(metadata_path),
        "detected_type": type_info.document_type,
        "sha256_hash": file_hash,
        "result": "imported",
    }
    append_csv_row(LOG_PATH, LOG_HEADERS, log_row)
    return log_row


def main() -> int:
    args = parse_args()
    files = expand_inputs(args.paths)
    if not files:
        print("No files found to import.")
        return 1

    max_ids = read_existing_ids()
    imported: list[dict[str, str]] = []
    for file_path in files:
        imported.append(import_file(file_path, max_ids))

    for row in imported:
        print(f"{row['evidence_id']} -> {row['destination_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
