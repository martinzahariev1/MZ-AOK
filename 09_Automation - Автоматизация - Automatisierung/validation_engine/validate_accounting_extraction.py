#!/usr/bin/env python3
"""Validate sampled accounting extraction rows against their source documents."""

from __future__ import annotations

import csv
import email
import html
import json
import random
import re
import sys
import zipfile
from collections import Counter, defaultdict
from email import policy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Accounting_Cash_Flow"
ORGANIZED_ROOT = REPO_ROOT / "00_INBOX - Входящи - Eingang" / "Accounting_Organized"
VALIDATION_CSV = REPORT_ROOT / "validation_results.csv"
VALIDATION_XLSX = REPORT_ROOT / "validation_results.xlsx"
VALIDATION_REPORT = REPORT_ROOT / "VALIDATION_REPORT.md"
RECOVERED_TEXT_ROOT = REPORT_ROOT / "recovered_health_insurance_text"
LOCAL_PACKAGES = REPO_ROOT / ".python_packages"
PDF_PASSWORD = "10001"
SAMPLE_SIZE = 20
RANDOM_SEED = 20260627

if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))

HEADERS = [
    "validation_id",
    "category",
    "sampled_row_number",
    "source_file",
    "source_readable",
    "fields_checked",
    "extracted_value",
    "actual_value",
    "validation_status",
    "evidence_found",
    "probable_parser_mistake",
    "recommended_fix",
    "notes",
]

CATEGORY_CONFIG = {
    "Payroll": {
        "file": REPORT_ROOT / "payroll_timeline.csv",
        "source_field": "source_documents",
        "fields": ["month", "total_brutto", "total_netto"],
    },
    "Health Insurance": {
        "file": REPORT_ROOT / "health_insurance_timeline.csv",
        "source_field": "source_documents",
        "fields": ["month", "insurance_name", "amount_due", "amount_paid", "unpaid_balance", "due_date", "late_fees"],
    },
    "Tax": {
        "file": REPORT_ROOT / "tax_timeline.csv",
        "source_field": "source_documents",
        "fields": ["month", "creditor", "tax_type", "amount_due", "amount_paid", "unpaid_balance", "due_date"],
    },
    "Operating Cost": {
        "file": REPORT_ROOT / "operating_costs_timeline.csv",
        "source_field": "source_documents",
        "fields": ["month", "category", "creditor", "amount_due", "amount_paid", "unpaid_balance"],
    },
    "Enrico": {
        "file": REPORT_ROOT / "enrico_cross_check.csv",
        "source_field": "source_file",
        "fields": ["month", "document_number", "document_type", "document_date", "amount"],
    },
}

OPERATING_CATEGORY_TERMS = {
    "fuel": ["fuel", "kraftstoff", "diesel", "benzin", "tank"],
    "vehicle costs": ["fahrzeug", "vehicle", "kfz", "auto"],
    "repairs": ["reparatur", "werkstatt", "repair"],
    "leasing": ["leasing"],
    "insurance": ["kfz-versicherung", "fahrzeugversicherung", "betriebshaftpflicht"],
    "rent": ["miete", "rent"],
    "phone": ["telefon", "phone", "mobilfunk"],
    "accounting fees": ["buchhaltung", "steuerberater", "accounting"],
    "equipment": ["ausstattung", "equipment", "scanner", "gerät", "geraet"],
    "car rental": ["mietwagen", "autovermietung", "car rental"],
}


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize(value: str) -> str:
    return (
        value.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("ъ", "u")
    )


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    return stem[:120] or "recovered_text"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def source_path(value: str) -> Path | None:
    if not value:
        return None
    first = value.split(";")[0].strip()
    if "::" in first:
        first = first.split("::", 1)[0]
    path = REPO_ROOT / Path(first)
    return path if path.exists() else None


def recovered_text_for(path: Path) -> str:
    candidate = RECOVERED_TEXT_ROOT / f"{safe_stem(path.name)}.txt"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8", errors="replace")
    return ""


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_pdf(path: Path) -> tuple[str, str]:
    recovered = recovered_text_for(path)
    if recovered.strip():
        return recovered, "recovered_text"
    errors: list[str] = []
    try:
        import fitz  # type: ignore

        doc = fitz.open(path)
        if doc.needs_pass and not doc.authenticate(PDF_PASSWORD):
            errors.append("fitz password failed")
        else:
            text = "\n".join(page.get_text("text") or "" for page in doc)
            if text.strip():
                return text, "fitz"
    except Exception as exc:
        errors.append(f"fitz failed: {exc}")
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(path), password=PDF_PASSWORD) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return text, "pdfplumber"
    except Exception as exc:
        errors.append(f"pdfplumber failed: {exc}")
    return "", " | ".join(errors)


def read_docx(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            texts: list[str] = []
            for name in archive.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    texts.append(re.sub(r"<[^>]+>", " ", archive.read(name).decode("utf-8", errors="replace")))
            return "\n".join(texts), "docx_xml"
    except Exception as exc:
        return "", f"docx failed: {exc}"


def read_xlsx(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            texts: list[str] = []
            for name in archive.namelist():
                if name.startswith("xl/") and name.endswith(".xml"):
                    texts.append(re.sub(r"<[^>]+>", " ", archive.read(name).decode("utf-8", errors="replace")))
            return "\n".join(texts), "xlsx_xml"
    except Exception as exc:
        return "", f"xlsx failed: {exc}"


def read_eml(path: Path) -> tuple[str, str]:
    try:
        with path.open("rb") as handle:
            message = email.message_from_binary_file(handle, policy=policy.default)
        parts = [message.get("date", ""), message.get("from", ""), message.get("to", ""), message.get("subject", "")]
        for part in message.walk() if message.is_multipart() else [message]:
            if part.get_content_type() in {"text/plain", "text/html"}:
                try:
                    parts.append(str(part.get_content()))
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
            filename = part.get_filename()
            if filename:
                parts.append(filename)
        return "\n".join(parts), "eml"
    except Exception as exc:
        return "", f"eml failed: {exc}"


def read_source(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(path)
    if suffix in {".txt", ".csv"}:
        return read_text_file(path), "text"
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".xlsx":
        return read_xlsx(path)
    if suffix == ".eml":
        return read_eml(path)
    return "", f"unsupported source type: {suffix}"


def amount_variants(value: str) -> set[str]:
    cleaned = re.sub(r"[^\d,.\-]", "", value or "")
    if not cleaned:
        return set()
    variants = {cleaned, cleaned.replace(".", ","), cleaned.replace(",", ".")}
    try:
        normalized = cleaned
        if "," in normalized and "." in normalized and normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        number = float(normalized)
        variants.add(f"{number:.2f}")
        variants.add(f"{number:.2f}".replace(".", ","))
        german = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        variants.add(german)
    except ValueError:
        pass
    return {item for item in variants if item}


def month_variants(month: str) -> set[str]:
    match = re.match(r"^(20\d{2})-(\d{2})$", month or "")
    if not match:
        return {month} if month else set()
    year, mon = match.groups()
    return {f"{year}-{mon}", f"{mon}-{year}", f"{mon}.{year}", f"{year}_{mon}", f"{mon}_{year}", f"{mon}/{year}"}


def supported(field: str, value: str, haystack: str) -> bool:
    if not value:
        return True
    normalized_haystack = normalize(haystack)
    if field == "month":
        return any(normalize(variant) in normalized_haystack for variant in month_variants(value))
    if field in {"amount", "total_brutto", "total_netto", "amount_due", "amount_paid", "unpaid_balance", "late_fees"}:
        return any(variant in haystack for variant in amount_variants(value))
    if field == "category" and value in OPERATING_CATEGORY_TERMS:
        return any(normalize(term) in normalized_haystack for term in OPERATING_CATEGORY_TERMS[value])
    return normalize(value) in normalized_haystack


def trace_supports_row(row: dict[str, str], fields: list[str]) -> set[str]:
    snippet = row.get("source_snippet", "")
    supported_fields: set[str] = set()
    for field in fields:
        value = row.get(field, "")
        if value and supported(field, value, snippet):
            supported_fields.add(field)
    return supported_fields


def suspicious_amount(value: str, text: str) -> str:
    cleaned = re.sub(r"[^\d,.]", "", value or "")
    if not cleaned:
        return ""
    date_like = cleaned.replace(",", ".")
    if re.fullmatch(r"\d{1,2}\.\d{1,2}", date_like) and re.search(rf"\b{re.escape(date_like)}\.(?:20)?\d{{2}}\b", text):
        return "amount resembles a document date fragment"
    return ""


def infer_actual(category: str, row: dict[str, str], source: Path | None, text: str) -> str:
    if not source:
        return "source file not found"
    filename = source.name
    hints: list[str] = []
    month = row.get("month", "")
    if month and not supported("month", month, f"{filename}\n{text}"):
        path_months = sorted({match.group(0) for match in re.finditer(r"\b(?:20\d{2}[-_]\d{2}|\d{2}[-_]\d{4})\b", filename)})
        if path_months:
            hints.append(f"source filename month hint: {', '.join(path_months)}")
    for field in ["amount", "total_brutto", "total_netto", "amount_due", "amount_paid", "unpaid_balance", "late_fees"]:
        if row.get(field) and not supported(field, row[field], text):
            reason = suspicious_amount(row[field], text)
            hints.append(f"{field}: not found" + (f" ({reason})" if reason else ""))
    if category == "Enrico" and "09_Enrico_Forwarded" not in repo_relative(source):
        hints.append("source is not in Enrico_Forwarded category")
    return "; ".join(hints) or "sampled values are supported by source text/path"


def validate_row(category: str, row_number: int, row: dict[str, str], fields: list[str], source_field: str, validation_id: int) -> dict[str, str]:
    source = source_path(row.get(source_field, ""))
    text = ""
    method = ""
    if source:
        text, method = read_source(source)
    haystack = f"{repo_relative(source) if source else row.get(source_field, '')}\n{text}"
    checked = [field for field in fields if row.get(field)]
    trace_supported = trace_supports_row(row, fields)
    supported_fields = [field for field in checked if supported(field, row.get(field, ""), haystack) or field in trace_supported]
    unsupported_fields = [field for field in checked if field not in supported_fields]
    wrong_signals: list[str] = []
    partial_signals: list[str] = []

    if not source:
        partial_signals.append("source file not found")
    elif not text.strip() and source.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
        partial_signals.append(f"source not readable: {method}")
    if category == "Enrico" and source and "09_Enrico_Forwarded" not in repo_relative(source):
        wrong_signals.append("Enrico row source is outside Enrico_Forwarded evidence folder")
    for field in unsupported_fields:
        value = row.get(field, "")
        reason = suspicious_amount(value, text)
        if field == "month" or reason:
            wrong_signals.append(f"{field} unsupported" + (f": {reason}" if reason else ""))
        else:
            partial_signals.append(f"{field} not found in source")

    if wrong_signals:
        status = "WRONG"
    elif partial_signals or len(supported_fields) < len(checked):
        status = "PARTIAL"
    else:
        status = "CORRECT"

    extracted = {field: row.get(field, "") for field in fields if row.get(field, "")}
    actual = infer_actual(category, row, source, text)
    mistake = probable_mistake(category, wrong_signals, partial_signals, row, source)
    return {
        "validation_id": f"VAL-{validation_id:04d}",
        "category": category,
        "sampled_row_number": str(row_number),
        "source_file": repo_relative(source) if source else row.get(source_field, ""),
        "source_readable": "YES" if text.strip() else "NO",
        "fields_checked": "; ".join(checked),
        "extracted_value": json.dumps(extracted, ensure_ascii=False),
        "actual_value": actual,
        "validation_status": status,
        "evidence_found": f"supported fields: {', '.join(supported_fields) or 'none'}; unsupported fields: {', '.join(unsupported_fields) or 'none'}",
        "probable_parser_mistake": mistake,
        "recommended_fix": recommended_fix(category, mistake, wrong_signals, partial_signals),
        "notes": f"source read method: {method}",
    }


def probable_mistake(category: str, wrong: list[str], partial: list[str], row: dict[str, str], source: Path | None) -> str:
    joined = " ".join(wrong + partial).lower()
    if category == "Enrico" and source and "09_Enrico_Forwarded" not in repo_relative(source):
        return "Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents."
    if "date fragment" in joined:
        return "Amount parser is reading dates as monetary amounts."
    if "month unsupported" in joined:
        return "Month parser selected a nearby date or unrelated filename token."
    if "not readable" in joined:
        return "Source requires OCR or unlocked/exported text before validation."
    if partial:
        return "Extracted value was not directly found in the readable source text."
    return ""


def recommended_fix(category: str, mistake: str, wrong: list[str], partial: list[str]) -> str:
    if "too broad" in mistake:
        return "Restrict category detection to folder hints plus stronger Enrico/Sachsenpower terms."
    if "dates as monetary" in mistake:
        return "Require currency/label context around amounts and reject date-shaped values."
    if "Month parser" in mistake:
        return "Prefer Leistungszeitraum/document period labels and filename month patterns over first date token."
    if "OCR" in mistake:
        return "Run OCR/recovery before extraction and validation."
    if partial:
        return "Add field-specific validation patterns and source text snippets for this document type."
    return "No parser fix required for sampled row."


def sample_rows(rows: list[dict[str, str]]) -> list[tuple[int, dict[str, str]]]:
    indexed = list(enumerate(rows, start=2))
    rng = random.Random(RANDOM_SEED)
    if len(indexed) <= SAMPLE_SIZE:
        return indexed
    return sorted(rng.sample(indexed, SAMPLE_SIZE), key=lambda item: item[0])


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def col_name(index: int) -> str:
    result = ""
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def write_xlsx(path: Path, rows: list[dict[str, str]]) -> None:
    values = [HEADERS] + [[str(row.get(header, "")) for header in HEADERS] for row in rows]
    sheet_rows: list[str] = []
    for row_index, row_values in enumerate(values, start=1):
        cells: list[str] = []
        for col_index, value in enumerate(row_values, start=1):
            ref = f"{col_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(sheet_rows) + "</sheetData></worksheet>"
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Validation" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def accuracy(rows: list[dict[str, str]]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for category in CATEGORY_CONFIG:
        category_rows = [row for row in rows if row["category"] == category]
        counts = Counter(row["validation_status"] for row in category_rows)
        total = len(category_rows)
        summary[category] = {
            "total": total,
            "correct": counts["CORRECT"],
            "partial": counts["PARTIAL"],
            "wrong": counts["WRONG"],
            "accuracy": round((counts["CORRECT"] / total * 100) if total else 0, 1),
        }
    return summary


def ranked_improvements(rows: list[dict[str, str]]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for row in rows:
        if row["validation_status"] in {"WRONG", "PARTIAL"}:
            counts[row["recommended_fix"]] += 1
    return counts.most_common()


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def write_report(rows: list[dict[str, str]]) -> None:
    summary = accuracy(rows)
    overall_total = len(rows)
    overall_correct = sum(1 for row in rows if row["validation_status"] == "CORRECT")
    overall_accuracy = round((overall_correct / overall_total * 100) if overall_total else 0, 1)
    wrong_rows = [row for row in rows if row["validation_status"] == "WRONG"]
    partial_rows = [row for row in rows if row["validation_status"] == "PARTIAL"]
    summary_rows = [
        [category, str(stats["correct"]), str(stats["partial"]), str(stats["wrong"]), f"{stats['accuracy']}%"]
        for category, stats in summary.items()
    ]
    wrong_table = [
        [row["category"], row["source_file"], row["extracted_value"], row["actual_value"], row["probable_parser_mistake"]]
        for row in wrong_rows
    ]
    improvements = [[fix, str(count)] for fix, count in ranked_improvements(rows)]
    report = f"""# Validation Report

## Scope

Validation sampled up to 20 existing rows per major category from current CSV outputs. It used only `Accounting_Organized`, existing report CSV/XLSX outputs, recovered text files, and processing logs/reports. No analyzer code or extracted tables were modified by the validation engine.

## Overall Accuracy

- Sampled rows: {overall_total}
- Overall extraction accuracy: {overall_accuracy}%
- Incorrect rows: {len(wrong_rows)}
- Partial rows: {len(partial_rows)}

## Accuracy By Category

{markdown_table(['Category', 'Correct', 'Partial', 'Wrong', 'Accuracy'], summary_rows)}

## Wrong Extractions

{markdown_table(['Category', 'Source file', 'Extracted value', 'Actual/source evidence', 'Probable parser mistake'], wrong_table) if wrong_table else '- None'}

## Parser Improvements Ranked By Impact

{markdown_table(['Recommended fix', 'Affected sampled rows'], improvements) if improvements else '- No parser improvements required by sampled rows.'}

## Method

- `CORRECT`: sampled key fields were directly supported by source text/path.
- `PARTIAL`: source was unreadable or only some key fields were directly supported.
- `WRONG`: source text/path clearly contradicted the row or showed a category/field parser mistake.
- Random seed: `{RANDOM_SEED}`.
"""
    VALIDATION_REPORT.write_text(report, encoding="utf-8")


def validate() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    validation_id = 1
    for category, config in CATEGORY_CONFIG.items():
        rows = read_csv(config["file"])
        for row_number, row in sample_rows(rows):
            results.append(validate_row(category, row_number, row, config["fields"], config["source_field"], validation_id))
            validation_id += 1
    return results


def main() -> int:
    results = validate()
    write_csv(VALIDATION_CSV, results)
    write_xlsx(VALIDATION_XLSX, results)
    write_report(results)
    summary = accuracy(results)
    overall = round((sum(1 for row in results if row["validation_status"] == "CORRECT") / len(results) * 100) if results else 0, 1)
    print(f"Overall extraction accuracy: {overall}%")
    for category, stats in summary.items():
        print(f"{category}: {stats['accuracy']}% ({stats['correct']} correct, {stats['partial']} partial, {stats['wrong']} wrong)")
    print(f"Incorrect rows: {sum(1 for row in results if row['validation_status'] == 'WRONG')}")
    print(f"Partial rows: {sum(1 for row in results if row['validation_status'] == 'PARTIAL')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
