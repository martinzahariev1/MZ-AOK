# Enrico Financial Deduction Analyzer

## Purpose

This tool analyzes Enrico Weissflog / Sachsenpower financial documents for the period `02.2024` to `06.2025` and generates monthly deduction tables.

It focuses on reliable evidence registration and conservative extraction. It does not perform OCR and does not invent numbers.

## Run

From this folder:

```powershell
python analyze_enrico_deductions.py
```

From the repository root:

```powershell
python "09_Automation - Автоматизация - Automatisierung/enrico_deduction_analyzer/analyze_enrico_deductions.py"
```

## Input Folders

The script recursively scans:

- `00_INBOX - Входящи - Eingang/Enrico`
- `_INBOX`
- `03_Documents - Документи - Dokumente`

Supported file types:

- `.pdf`
- `.zip`
- `.rar`
- `.txt`
- `.csv`
- `.eml`

ZIP and RAR archives are extracted only into a temporary processing folder. Original files are never modified.

## Output Folder

Outputs are written to:

`08_Reports - Доклади - Berichte/Enrico_Deductions`

Generated files:

- `enrico_deductions_monthly.csv`
- `enrico_deductions_monthly.xlsx`
- `enrico_deductions_detailed.csv`
- `enrico_deductions_detailed.xlsx`
- `missing_months.csv`
- `duplicate_documents.csv`
- `processing_log.txt`
- `README.md`
- `ENRICO_DEDUCTION_ANALYSIS.md`

## Optional Dependencies

The script uses the Python standard library for CSV, EML, ZIP, logging, deduplication, and basic XLSX generation.

For better extraction, install:

```powershell
pip install -r requirements.txt
```

Optional dependency notes:

- `pypdf` improves PDF text extraction.
- `pdfplumber` is used as a fallback when `pypdf` cannot extract text.
- `rarfile` enables RAR reading, but may also require a local RAR backend.
- `pandas` and `openpyxl` are available for future spreadsheet expansion; this version can generate simple `.xlsx` files without them.
- `beautifulsoup4` improves HTML email body extraction.

If global Python package installation is unavailable, the script also checks for packages in a repository-local `.python_packages` folder.

## Detection Targets

The analyzer looks for:

- `Gutschrift`
- `Rechnung`
- `Leistungsnachweis`
- `Sendungsverlust`
- `Rückerstattung`
- `Rechnungskorrektur`
- `Scannermiete`
- `Abschlag Coincident`
- `Abschlag Mitnahme`
- `Abschlag Quittungslose Sendung`

Tracked deduction categories:

- `Abschlag Coincident`
- `Abschlag Mitnahme`
- `Abschlag Quittungslose Sendung`
- `Sendungsverlust`
- `Scannermiete`
- `Scanner-related invoices`
- `Other deductions`

## Limits

- OCR is not implemented.
- Scanned PDFs without embedded text will produce LOW confidence or empty values.
- RAR extraction depends on optional local support.
- Values that cannot be extracted are left empty.
