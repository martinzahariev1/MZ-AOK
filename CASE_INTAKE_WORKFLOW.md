# Case Intake Workflow

## Purpose

This workflow defines how new evidence is added to the repository. It is designed to keep every document traceable, searchable, and usable by investigators, lawyers, accountants, insolvency administrators, and AI systems.

## Core Rules

- Never overwrite original evidence.
- Never modify original evidence.
- Preserve the original filename in metadata.
- Assign a unique evidence ID before analysis or reporting.
- Every action must be traceable.
- Every important fact must link back to evidence IDs.
- Use evidence IDs as the main reference, not filenames.

## Intake Steps for Every New Document

### 1. Assign Unique Evidence ID

Assign the correct ID based on the evidence type.

Examples:

- `DOC-000001`
- `MAIL-000001`
- `CHAT-000001`
- `BANK-000001`
- `PAY-000001`
- `PHOTO-000001`
- `COURT-000001`
- `POLICE-000001`

The ID must be unique and must not be reused.

### 2. Preserve Original Filename

Record the original filename exactly as received.

Required metadata:

- original filename
- source location
- received date
- received method
- person or system that added the file

### 3. Copy Original File Into the Correct Folder

Copy the original file into the most specific folder available.

Examples:

- court documents go under `03_Documents - Документи - Dokumente/Court - Съд - Gericht`
- bank statements go under `03_Documents - Документи - Dokumente/Bank - Банка - Bank`
- WhatsApp exports go under `03_Documents - Документи - Dokumente/WhatsApp - WhatsApp - WhatsApp`
- health insurance documents go under `03_Documents - Документи - Dokumente/Health Insurance - Здравни каси - Krankenkassen`

If no specific folder fits, use `Other - Други - Sonstiges` temporarily and add a note explaining why.

### 4. Record Metadata

Record metadata in the correct dashboard tracker.

Minimum metadata:

- evidence ID
- date
- source
- language
- classification
- confidence
- original filename
- current filename
- file location
- summary
- related people
- related companies
- related events
- related evidence
- keywords
- notes

Recommended integrity metadata:

- SHA-256 hash
- file size
- date received
- date added
- added by
- chain-of-custody notes
- derived-from evidence ID, if applicable

### 5. Link to Timeline, People, Companies, and Related Evidence

Connect the document to existing records.

Update or create links to:

- timeline entries
- event IDs
- person IDs
- company IDs
- claim IDs
- related evidence IDs

If a related item does not yet exist, create a placeholder entry or add a follow-up note.

### 6. Generate Short Factual Summary

Write a short factual summary based only on the document content.

The summary should state:

- who created or sent the document
- who received it
- what the document says
- what date or period it concerns
- what amounts, deadlines, claims, or decisions appear

Do not include unsupported conclusions in the factual summary.

### 7. Extract Important Dates

Identify and record all relevant dates.

Examples:

- document date
- received date
- payment date
- deadline
- contract period
- employment period
- court date
- insolvency deadline
- insurance coverage period

Each important date should link to a timeline entry when relevant.

### 8. Extract People

Identify all people mentioned in the document.

For each person, record where known:

- name
- role
- organization
- contact information
- related person ID
- relationship to the case

Create a new `PERSON-000001` style ID if the person is important and does not already exist.

### 9. Extract Companies

Identify all companies, institutions, authorities, or organizations mentioned.

For each company, record where known:

- name
- role
- registration number
- tax number
- address
- contact person
- related company ID
- relationship to the case

Create a new `COMP-000001` style ID if the company is important and does not already exist.

### 10. Extract Locations

Identify all relevant locations.

Examples:

- company address
- court location
- police office
- tax office
- bank branch
- workplace
- delivery location
- meeting location

Record locations in metadata or notes when they help establish facts, jurisdiction, responsibility, or financial relevance.

### 11. Extract Legal References

Identify legal references, case numbers, court references, administrative references, and formal deadlines.

Examples:

- statute references
- court case numbers
- police case numbers
- tax office reference numbers
- insolvency case numbers
- legal deadlines
- administrative decisions

Link legal references to the legal folder, claims, timeline entries, or related evidence where relevant.

### 12. Identify Possible Financial Relevance

Check whether the document affects money, claims, deductions, liabilities, or accounting.

Examples:

- invoice amount
- salary amount
- payment confirmation
- unpaid claim
- deduction
- bank transfer
- tax amount
- insurance contribution
- insolvency claim
- reimbursement demand

If financially relevant, link the document to payments, claims, deductions, invoices, payroll, or finance analysis.

### 13. Classify the Document's Case Impact

Identify whether the document:

- introduces new facts
- supports existing facts
- contradicts existing facts
- requires follow-up

Multiple classifications may apply.

Record the result in metadata or notes.

### 14. Update Dashboard Statistics

Update dashboard statistics and trackers after intake.

Examples:

- total documents
- total evidence items
- new timeline events
- new people
- new companies
- new claims
- unverified evidence count
- follow-up required count
- documents by source
- documents by language
- documents by classification

Dashboard statistics must be based on recorded metadata, not guesswork.

### 15. Never Overwrite Original Evidence

If a new version, correction, translation, OCR output, or annotation is created:

- keep the original file unchanged
- create a new derived file
- assign or reference the correct evidence ID
- record the relationship to the original file
- update metadata

### 16. Ensure Every Action Is Traceable

Every intake action must leave a record.

Traceability should answer:

- what was added
- when it was added
- who or what added it
- where it came from
- where it is stored
- which evidence ID identifies it
- which metadata describes it
- which timeline, people, companies, claims, and evidence it links to
- what follow-up is required

## Intake Quality Checklist

Before finishing intake, confirm:

- evidence ID assigned
- original filename preserved
- original file copied to the correct folder
- metadata recorded
- factual summary written
- important dates extracted
- people extracted
- companies extracted
- locations extracted
- legal references extracted
- financial relevance checked
- related timeline entries linked
- related people linked
- related companies linked
- related evidence linked
- case impact classified
- dashboard statistics updated
- original evidence preserved
- actions are traceable

## Follow-Up Rules

Create a follow-up note when:

- source is unclear
- date is missing or uncertain
- sender or recipient is unidentified
- financial amount cannot be matched
- legal reference needs review
- translation is required
- OCR is required
- document contradicts existing evidence
- document appears incomplete
- duplicate evidence is suspected

Follow-up notes should cite the evidence ID and explain the missing action.

