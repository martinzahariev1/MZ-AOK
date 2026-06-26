# Accounting File Organizer

## Purpose

Organizes accounting inbox files into category folders before financial extraction.

The organizer copies files from:

`00_INBOX - Входящи - Eingang/Accounting`

to:

`00_INBOX - Входящи - Eingang/Accounting_Organized`

Original files are never deleted or overwritten.

## Run

```powershell
python "09_Automation - Автоматизация - Automatisierung/accounting_file_organizer/organize_accounting_files.py"
```

## Outputs

Inside `Accounting_Organized`:

- category folders
- `file_organization_manifest.csv`
- `file_organization_manifest.xlsx`
- `duplicate_files.csv`
- `unknown_files.csv`
- `organization_log.txt`
- `ACCOUNTING_FILE_ORGANIZATION_REPORT.md`

