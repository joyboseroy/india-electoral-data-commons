# Processed Data

CSVs extracted from Form 20 PDFs using analysis/extract_form20_pdf.py.

## Verification requirement

Every CSV in this folder must have been verified against the EVM-votes
summary row in the corresponding Form 20 PDF footer before being committed.
Note the verification status in the table below.

## Files in this folder

| File | Source PDF | Booths | Verified totals |
|------|-----------|--------|----------------|
| delhi_2013_AC50_greater_kailash.csv | delhi_2013_AC50_greater_kailash.pdf | 156 | BJP 29,897 / INC 19,641 / AAP 42,924 — exact match |

## Column format

All CSVs follow this structure:

```
part_no, bjp_votes, inc_votes, aap_votes, others_votes, nota_votes, total_votes
```

Party column names vary by constituency depending on which parties
contested. `nota_votes` and `total_votes` are always present.
`part_no` is the polling station serial number from Form 20.

Postal votes are excluded — they appear as a separate summary row in
Form 20 and cannot be attributed to individual polling stations.
