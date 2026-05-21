# Statement Validation Dataset Spec

## Goal

This dataset is for the `statement` scene when the product needs more than a single visual demo.
It is meant to support:

- field extraction checks
- receipt-to-bank matching checks
- mismatch and missing-item checks
- stable Step3 card rendering with enough examples

It is not a legal or tax dataset. It is an evaluation dataset for document parsing and matching.

## Minimum dataset size

For the first usable version, prepare at least:

- 12 receipt files
- 1 to 3 bank statement files covering the same date range
- 1 ground-truth table

Recommended split:

- 8 clearly matchable receipts
- 2 receipts with partial ambiguity
- 2 receipts with no matching bank entry

This gives enough coverage for all four Step3 cards:

1. receipt extraction result
2. comparison conclusion
3. detailed comparison and suspicious points
4. quality and completeness metrics

## Required source files

Each dataset batch should contain:

### Receipts

Each receipt should expose as many of these fields as possible:

- receipt id or ticket id
- merchant
- date
- amount
- origin
- destination
- payment method
- note or purpose

Formats allowed:

- PDF
- JPG
- PNG

### Bank statements

The statement side should contain:

- account name
- statement period
- transaction date
- transaction description
- debit or credit direction
- amount

Preferred format:

- PDF

Optional working source:

- XLSX

## Ground truth requirements

The dataset must include a ground-truth table.
Without this file, you can demo matching, but you cannot do metric validation.

Each receipt row should answer:

- which bank statement file is relevant
- whether a true matching transaction exists
- which transaction row is the intended match
- whether date matches
- whether amount matches
- whether merchant or description is semantically aligned
- whether the receipt is complete enough for archival use

## Minimum fields for the ground-truth table

Use these columns:

- `receipt_id`
- `receipt_file`
- `statement_file`
- `expected_match`
- `expected_transaction_id`
- `receipt_date`
- `expected_date`
- `date_match`
- `receipt_amount`
- `expected_amount`
- `amount_match`
- `receipt_merchant`
- `expected_description`
- `merchant_match`
- `completeness_grade`
- `archive_ready`
- `notes`

## Suggested label values

Use stable values to keep later scoring simple:

- `expected_match`: `yes` / `no`
- `date_match`: `yes` / `no` / `partial`
- `amount_match`: `yes` / `no`
- `merchant_match`: `yes` / `no` / `partial`
- `completeness_grade`: `high` / `medium` / `low`
- `archive_ready`: `yes` / `no`

## Coverage rules

The dataset should intentionally contain these cases:

### A. Clean matches

- receipt date equals bank date
- receipt amount equals bank amount
- merchant wording is close enough to match

### B. Fuzzy matches

- merchant wording differs but obviously refers to the same trip or vendor
- receipt has a short merchant name, statement has a longer service description

### C. No-match cases

- receipt exists but no corresponding bank transaction appears
- bank statement contains nearby amounts that should not match

### D. Incomplete receipt cases

- missing merchant
- missing amount
- missing date
- unreadable route or purpose

These cases are necessary if you want metrics that mean anything.

## Metrics that this dataset can support

Once the ground truth exists, this dataset can support:

- field hit count
- field completeness rate
- date readability rate
- amount readability rate
- true-match hit rate
- false-match rate
- archive readiness rate

This is the correct scope for the current product.

## Metrics that this dataset should not claim

Do not present these as authoritative:

- tax filing advice
- reimbursement compliance approval
- formal accounting verification
- legal audit conclusion

## Folder layout

Use the following structure:

```text
demo_sample_files_public/
  validation_datasets/
    statement_eval/
      README.md
      manifest.csv
      ground_truth.csv
      receipts/
      statements/
      rendered/
```

## File naming rules

Use stable file names:

- receipts: `receipt_001.pdf`, `receipt_002.jpg`
- statements: `statement_2025_01_a.pdf`
- rendered previews: `receipt_001_p1.png`, `statement_2025_01_a_p1.png`

Avoid human-renamed one-off files like `final-new-latest2.pdf`.

## Acceptance checklist

The first dataset version is acceptable only if:

- there are at least 12 receipts
- there is at least one complete bank statement covering the same period
- every receipt has a row in `ground_truth.csv`
- at least 8 rows are clean positive matches
- at least 2 rows are intentional no-match cases
- at least 2 rows are incomplete or ambiguous cases

## Immediate next step

The current taxi receipt plus one bank statement page is useful as a UI demo pair.
It is not enough for metric validation.

To upgrade from demo to evaluation:

1. collect 12 to 20 receipts from the same date range
2. collect the matching bank statement pages
3. fill `ground_truth.csv`
4. keep a few intentionally bad or unmatched samples
