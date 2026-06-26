# Evidence Import Tool

## Purpose

`import_evidence.py` registers new evidence files without OCR, content parsing, or analysis. It focuses only on reliable evidence intake.

The tool:

- detects file type from filename and extension
- assigns the next evidence ID
- preserves the original filename in metadata
- copies the original file into the evidence folder
- creates JSON metadata
- updates `documents.csv`
- leaves analysis fields empty
- never overwrites existing evidence
- logs every import

## Location

Run the tool from anywhere inside the repository:

```powershell
python "09_Automation - Автоматизация - Automatisierung/Evidence Import Tool - Импорт на доказателства - Beweisimport/import_evidence.py" "C:\path\to\document.pdf"
```

## Usage Examples

Import one file:

```powershell
python "09_Automation - Автоматизация - Automatisierung/Evidence Import Tool - Импорт на доказателства - Beweisimport/import_evidence.py" "C:\Evidence\aok-letter.pdf"
```

Import multiple files:

```powershell
python "09_Automation - Автоматизация - Automatisierung/Evidence Import Tool - Импорт на доказателства - Beweisimport/import_evidence.py" "C:\Evidence\aok-letter.pdf" "C:\Evidence\bank-statement.pdf"
```

Import every file in a folder:

```powershell
python "09_Automation - Автоматизация - Automatisierung/Evidence Import Tool - Импорт на доказателства - Beweisimport/import_evidence.py" "C:\Evidence\Incoming"
```

Import by pattern:

```powershell
python "09_Automation - Автоматизация - Automatisierung/Evidence Import Tool - Импорт на доказателства - Beweisimport/import_evidence.py" "C:\Evidence\Incoming\*.pdf"
```

## Output

For each imported file, the tool creates:

- a copied evidence file under `02_Evidence - Доказателства - Beweismittel`
- a matching `.metadata.json` file next to the copied evidence file
- a new row in `00_Case Dashboard - Табло на случая - Fallübersicht/documents.csv`
- a new row in `import_log.csv`

## Evidence ID Prefixes

- `DOC` for general documents
- `MAIL` for email files
- `CHAT` for chat or WhatsApp files
- `BANK` for bank records
- `PAY` for payment records
- `PHOTO` for photos and images
- `COURT` for court documents
- `POLICE` for police documents

## Important Limits

This first version does not:

- perform OCR
- parse document contents
- extract people, companies, dates, amounts, or legal references
- generate analysis
- verify facts inside the document

All summary, relationship, language, source, and notes fields are intentionally left empty for later human or AI review.

