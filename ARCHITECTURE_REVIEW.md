# Architecture Review

## Scope

This review assesses the current repository as a long-term professional Evidence Management System intended to support thousands of documents, multilingual material, financial records, legal analysis, and future automation.

## Overall Assessment

The repository has a strong initial architecture. It already separates major case functions into numbered folders, uses multilingual folder names, provides dashboard CSV templates, and defines basic naming rules. This is a good foundation for disciplined evidence work.

The main architectural gap is that the system currently mixes storage categories with evidence lifecycle stages. For a small case this is manageable. For thousands of files, the repository will need stronger separation between original evidence, processed copies, extracted data, analysis, and final reports. It will also need stricter identifiers, integrity controls, and automation-ready metadata.

## Strengths

### Folder Hierarchy

- The numbered root folders create a predictable navigation model.
- The main domains are sensible: dashboard, timeline, evidence, documents, entities, finance, legal, analysis, reports, automation, and archive.
- The `03_Documents - Документи - Dokumente` folder has useful source and category subfolders for common case document types.
- The dashboard folder provides a central place for indexes and CSV trackers.

### Naming Consistency

- The multilingual folder naming rule is clear and human-friendly.
- The filename pattern `YYYY-MM-DD_Source_Type_Short-description_Language_Status.ext` is practical for sorting and searching.
- Standard language and status values already exist.
- Date-first filenames will work well in normal file explorers and command-line searches.

### Searchability

- CSV trackers create a structured search layer beyond raw folders.
- The proposed fields in `documents.csv`, `evidence.csv`, `timeline.csv`, and related trackers are useful starting points.
- Separating emails, WhatsApp messages, bank records, payroll, court, police, and insurance records improves targeted search.

### Future Automation

- The `09_Automation - Автоматизация - Automatisierung` folder gives automation a dedicated place.
- CSV headers are simple enough for scripts, spreadsheets, and later database import.
- The repository already has a naming standard that automation can validate.

### Evidence Integrity

- The current guide tells users to keep original evidence unchanged whenever possible.
- `evidence.csv` includes a `hash` field, which is important for proving that files have not changed.
- The workflow encourages recording source documents and related evidence.

## Weaknesses

### Original Evidence vs Derived Material

The current structure does not clearly separate:

- original evidence
- working copies
- OCR output
- translations
- extracted data
- analysis notes
- final reports

For example, `02_Evidence - Доказателства - Beweismittel` may contain both primary evidence and evidence summaries. `03_Documents - Документи - Dokumente` may contain originals, copies, and processed documents together. This can become risky when the repository grows.

### Scale Limits

The structure is suitable for hundreds of documents, but thousands of documents may create problems:

- Large category folders can become crowded.
- Filename-only organization may not be enough for versioning, duplicates, and cross-references.
- Manual CSV updates can become error-prone.
- Some folders may need year, month, source, or case-phase subdivisions.

### Evidence Integrity Controls

The system has a hash column, but it does not yet define:

- which hash algorithm to use
- when hashes are calculated
- whether hashes apply to originals only or also derived files
- how to record custody, source, collector, import date, and verification status
- how to handle duplicate files
- how to prevent accidental editing of originals

### Naming Ambiguity

The current filename pattern is good but may become ambiguous at scale:

- `Source` may vary by spelling, abbreviation, or person.
- `Type` is not controlled by a formal vocabulary.
- `Short-description` can drift over time.
- `Status` mixes evidence state (`original`, `copy`) with work state (`draft`, `final`).

This makes automation harder unless controlled values are introduced.

### Multilingual Path Length and Tool Compatibility

The multilingual folder names are readable, but they create long paths. On Windows, deeply nested folders with long filenames may approach path length limits in some tools. Cyrillic and German characters are appropriate for human use, but some command-line tools or legacy systems may misrender them unless UTF-8 handling is configured consistently.

### Dashboard CSVs as Primary Indexes

CSV templates are useful, but CSVs alone can become fragile:

- no enforced unique IDs
- no relationships enforced between files
- no validation of status or language values
- no audit trail for changed rows
- no automated check that listed files actually exist

For thousands of records, CSVs should be treated as portable indexes, not the only source of truth.

### Archive Semantics

The archive folder exists, but archive rules are not yet strict enough. It is unclear whether archived files are inactive originals, superseded drafts, duplicate exports, or historical snapshots. Mixing those together can weaken evidence traceability.

## Recommendations

### 1. Add Evidence Lifecycle Separation

Consider introducing a lifecycle model inside evidence and documents:

- `Originals`
- `Working Copies`
- `OCR`
- `Translations`
- `Extracted Data`
- `Annotations`
- `Exports`

This would make it clearer which files are untouched source material and which files are derived.

### 2. Strengthen Evidence IDs

Use stable IDs for every evidence item, for example:

`EV-000001`

Then include the ID in:

- `evidence.csv`
- related dashboard CSVs
- analysis notes
- reports
- optionally filenames for high-value evidence

This improves citation, deduplication, and automation.

### 3. Define Controlled Vocabularies

Create controlled value lists for:

- document type
- source
- category
- language
- status
- evidence sensitivity
- verification state
- relationship type
- claim type

This will reduce spelling drift and make filtering reliable.

### 4. Separate Evidence Status from Work Status

The current `Status` field mixes concepts. Consider separating it into:

- `evidence_state`: `original`, `copy`, `derived`, `translation`, `ocr`, `annotation`
- `work_status`: `new`, `reviewed`, `verified`, `needs_followup`, `final`

This will make evidence integrity easier to reason about.

### 5. Expand Integrity Metadata

For evidence-grade tracking, `evidence.csv` should eventually include:

- `evidence_id`
- `sha256_hash`
- `file_size_bytes`
- `original_filename`
- `current_filename`
- `source`
- `collector`
- `date_received`
- `date_created`
- `storage_location`
- `chain_of_custody_notes`
- `verification_status`
- `duplicate_of`

Use SHA-256 as the default hash algorithm unless a legal process requires another standard.

### 6. Add Automation Validation

Future automation should be able to check:

- every indexed file exists
- every evidence file is indexed
- every evidence ID is unique
- filenames match the naming pattern
- hashes match current files
- required CSV fields are populated
- folder names follow the multilingual naming rule
- no original evidence file was modified after intake

### 7. Introduce Scalable Subdivision Rules

For large folders, define subdivision rules before files accumulate. Good candidates:

- by year: `2026`, `2027`
- by source: `AOK`, `Finanzamt`, `Court`
- by person or company ID
- by case phase
- by evidence ID range, such as `EV-000001_to_EV-000999`

The best choice depends on actual document volume and retrieval habits.

### 8. Keep Reports Reproducible

Reports should cite evidence IDs and source files. Final reports should not be the only place where conclusions exist. Each report should be traceable back to:

- source evidence
- extracted data
- timeline entries
- analysis notes
- claims or legal issues

### 9. Treat Archive as a Governance Area

Define archive categories, for example:

- `Superseded Drafts`
- `Duplicate Exports`
- `Closed Issues`
- `Historical Snapshots`

Original evidence should generally remain in the original evidence area, not in archive, unless there is a documented reason.

## Proposed Improvements

These are proposed only and are not implemented in this review.

### Proposed Folder Additions

- Add `Originals - Оригинали - Originale` under evidence or documents.
- Add `Derived - Производни - Abgeleitete Dateien` for OCR, translations, annotations, and extracted data.
- Add `Registers - Регистри - Register` under the dashboard for controlled vocabulary tables.
- Add `Integrity - Цялост - Integrität` for hash manifests and verification logs.
- Add `Imports - Импорт - Importe` under automation for raw import batches and processing logs.

### Proposed Root Files

- `CHAIN_OF_CUSTODY.md`
- `CONTROLLED_VOCABULARY.md`
- `HASHING_POLICY.md`
- `DATA_DICTIONARY.md`
- `AUTOMATION_CHECKS.md`

### Proposed CSV Enhancements

- Add `sha256_hash` instead of generic `hash`.
- Add `created_at`, `updated_at`, and `reviewed_by` fields where useful.
- Add `source_file_path` and `derived_from_evidence_id`.
- Add unique IDs to all relationship-heavy tables.
- Add validation rules for required fields and controlled values.

### Proposed Automation Roadmap

1. Validate folder naming and required README files.
2. Validate CSV headers and required fields.
3. Generate SHA-256 manifests for original evidence.
4. Detect unindexed files and missing files.
5. Generate timeline views from `timeline.csv`.
6. Generate evidence packets for reports from evidence IDs.
7. Create duplicate detection by hash and filename similarity.

## Suitability for Thousands of Documents

The current repository is a good first version for manual evidence organization. It is not yet fully ready for thousands of documents without additional governance. The architecture can scale if the next phase adds stricter evidence lifecycle folders, unique IDs, controlled vocabularies, hash manifests, validation scripts, and clear rules for originals versus derived files.

The strongest next move is to protect original evidence with a dedicated original-evidence area and a hash-based integrity process before large-scale intake begins.

