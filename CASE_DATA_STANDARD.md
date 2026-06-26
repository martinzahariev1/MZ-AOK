# Case Data Standard

## Purpose

This document defines the repository-wide data standard for managing case evidence, documents, people, companies, events, claims, timelines, analysis, reports, and automation-ready metadata.

The standard is designed for use by:

- investigators
- lawyers
- accountants
- insolvency administrators
- AI systems

## Core Principles

- Never modify original evidence.
- Always preserve originals.
- Always reference evidence IDs instead of filenames.
- Everything must be traceable from report, analysis, or claim back to source evidence.
- Every important file or record must have a stable ID.
- Filenames help humans search, but IDs are the authoritative references.
- Derived files must always identify the original evidence they came from.

## Evidence IDs

Every evidence item must receive a unique ID. The ID prefix identifies the evidence category.

### Standard Evidence ID Formats

- `DOC-000001` for general documents
- `MAIL-000001` for emails
- `CHAT-000001` for chat or WhatsApp messages
- `BANK-000001` for bank records
- `PAY-000001` for payment records
- `PHOTO-000001` for photos, screenshots, and images
- `COURT-000001` for court documents
- `POLICE-000001` for police documents

### Evidence ID Rules

- IDs must be unique across their category.
- IDs must not be reused after deletion, replacement, or archiving.
- IDs must be assigned at intake before analysis or reporting.
- Derived evidence must reference the original evidence ID.
- Reports, timelines, claims, and analysis must cite evidence IDs, not only filenames.

## Person IDs

Every relevant person must receive a stable person ID.

Format:

`PERSON-000001`

Person IDs apply to:

- employees
- company representatives
- lawyers
- accountants
- investigators
- witnesses
- public authority contacts
- other relevant individuals

## Company IDs

Every relevant company, institution, authority, or organization must receive a stable company ID.

Format:

`COMP-000001`

Company IDs apply to:

- companies
- partner companies
- banks
- health insurance funds
- tax offices
- courts
- police offices
- insolvency administrators
- public authorities

## Event IDs

Every important factual event must receive a stable event ID.

Format:

`EVENT-000001`

Event IDs apply to:

- signed agreements
- payments
- deductions
- letters received
- emails sent or received
- phone calls
- meetings
- court filings
- deadlines
- disputes
- insolvency events

## Claim IDs

Every claim, demand, dispute item, or financial/legal position must receive a stable claim ID.

Format:

`CLAIM-000001`

Claim IDs apply to:

- payment claims
- salary claims
- insurance contribution claims
- tax claims
- deductions
- damages
- reimbursement demands
- legal objections
- insolvency claims

## Timeline IDs

Every timeline entry must receive a stable timeline ID.

Format:

`TIME-000001`

Timeline IDs connect events to dates, evidence, people, companies, and claims.

## File Naming Convention

Every file must use the standard naming convention:

`YYYY-MM-DD_ID_Source_Type_Short-description_Language_Classification_Confidence.ext`

Example:

`2026-06-23_MAIL-000001_AOK_Email_Contribution-demand_DE_Original-Evidence_Verified.pdf`

## Filename Fields

- `YYYY-MM-DD`: date of the evidence, document, event, or report
- `ID`: stable evidence, person, company, event, claim, or timeline ID
- `Source`: short source name, such as `AOK`, `Bank`, `Court`, or `Partner-Company`
- `Type`: document or evidence type, such as `Email`, `Invoice`, `Statement`, `Filing`, or `Photo`
- `Short-description`: concise description using hyphens instead of spaces
- `Language`: `BG`, `DE`, `EN`, or `MIX`
- `Classification`: evidence or work classification
- `Confidence`: confidence level for factual reliability
- `ext`: original file extension

## File Naming Rules

- Use ISO dates: `YYYY-MM-DD`.
- Use the assigned ID in every important filename.
- Use hyphens inside the short description.
- Avoid special characters that may break tools.
- Preserve the original file extension.
- Do not rename originals unless the original filename is also recorded in metadata.
- Do not rely on filenames as the only reference.
- Use IDs in reports, notes, CSV rows, and analysis.

## Required Metadata for Every Evidence Item

Every evidence item must have metadata recorded in the relevant tracker.

### Required Fields

- `evidence_id`
- `date`
- `source`
- `language`
- `classification`
- `confidence`
- `original_filename`
- `current_filename`
- `file_location`
- `summary`
- `related_people`
- `related_companies`
- `related_events`
- `related_claims`
- `keywords`
- `notes`

### Recommended Integrity Fields

- `sha256_hash`
- `file_size_bytes`
- `date_received`
- `date_added`
- `added_by`
- `original_storage_location`
- `derived_from_evidence_id`
- `verification_status`
- `chain_of_custody_notes`

## Classification Levels

### Original Evidence

Untouched source material exactly as received or collected.

Examples:

- original PDF letter
- email export
- bank statement download
- court document received from court
- original screenshot

Rules:

- Must never be modified.
- Must be preserved.
- Should be hashed.
- Must be traceable to source and intake date.

### Derived Evidence

Files created from original evidence.

Examples:

- OCR text
- translated document
- cropped copy
- annotated PDF
- extracted table
- converted file format

Rules:

- Must reference the original evidence ID.
- Must not replace the original.
- Must clearly state how it was derived.

### Analysis

Interpretations, comparisons, contradictions, calculations, and conclusions based on evidence.

Examples:

- contradiction matrix
- legal issue note
- payment reconciliation
- claim assessment
- timeline interpretation

Rules:

- Must cite evidence IDs.
- Must separate facts from assumptions.
- Must record confidence where applicable.

### Generated Report

Formal or semi-formal output created for communication, submission, or review.

Examples:

- lawyer packet
- insolvency administrator report
- accountant summary
- evidence index
- final case report

Rules:

- Must cite evidence IDs.
- Must be reproducible from evidence, metadata, and analysis.
- Must have draft or final status.

### Working Notes

Temporary notes, intake notes, planning notes, and incomplete thoughts.

Examples:

- checklist
- meeting notes
- task notes
- draft observations

Rules:

- Must not be treated as evidence.
- Must be converted into analysis or metadata if relied on.
- Must cite evidence IDs when referring to evidence.

## Evidence Confidence

### Verified

The evidence or fact has been checked against source material and is reliable.

Examples:

- hash matches original file
- date and sender are visible
- bank transaction appears in official statement
- court document includes case number and court source

### Partially Verified

The evidence or fact is supported but not fully confirmed.

Examples:

- screenshot exists but original export is missing
- translation exists but has not been independently checked
- payment is mentioned in messages but not yet matched to a bank statement

### Unverified

The evidence or fact has not yet been confirmed.

Examples:

- unsourced claim
- incomplete file
- unidentified sender
- unclear date
- working note without supporting evidence

## Traceability Rules

- Every report must cite the evidence IDs it relies on.
- Every analysis document must cite the evidence IDs it relies on.
- Every claim must cite supporting and opposing evidence IDs.
- Every timeline entry must cite related event IDs and evidence IDs.
- Every derived file must cite the original evidence ID.
- Every person, company, claim, event, and timeline entry should be cross-referenced where relevant.

## Original Evidence Rules

- Never edit original evidence.
- Never overwrite original evidence.
- Never delete original evidence unless there is a documented legal or privacy reason.
- Store originals in their designated original evidence location.
- Record original filenames before renaming or copying.
- Prefer creating working copies for annotation, OCR, translation, or extraction.
- Hash originals as soon as possible after intake.

## AI System Rules

AI systems may assist with OCR, classification, summaries, extraction, translation, search, and report drafting.

AI-generated outputs must:

- be classified as `Derived Evidence`, `Analysis`, `Generated Report`, or `Working Notes`
- cite source evidence IDs
- include confidence levels where facts are extracted or inferred
- preserve uncertainty instead of inventing missing facts
- avoid replacing original evidence

AI systems must not:

- modify original evidence
- treat filenames as the only source of truth
- create unsupported conclusions
- remove traceability between source evidence and outputs

## Professional Use Rules

### Investigators

Investigators should use evidence IDs, event IDs, and metadata to reconstruct facts and identify missing evidence.

### Lawyers

Lawyers should cite evidence IDs in legal arguments, filings, issue lists, and correspondence.

### Accountants

Accountants should link payments, deductions, invoices, payroll records, and financial claims to evidence IDs and claim IDs.

### Insolvency Administrators

Insolvency administrators should use company IDs, claim IDs, payment records, and verified evidence IDs to assess claims and deadlines.

## Minimum Standard for Any Important Item

An important item is not considered properly entered until it has:

- a stable ID
- a date or estimated date
- a source
- a classification
- a confidence level
- a file location or record location
- a short summary
- related people or companies where known
- related event, claim, or timeline IDs where relevant
- notes explaining uncertainty or missing information

