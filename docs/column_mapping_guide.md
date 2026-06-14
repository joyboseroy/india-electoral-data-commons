# Form 20 Column Mapping Guide

The most common source of confusion when using `extract_form20_pdf.py`
is identifying the correct candidate column order in a Form 20 PDF.
This guide explains the process step by step.

---

## Understanding Form 20 table structure

A Form 20 table looks like this (simplified):

```
Serial No. | Cand A | Cand B | Cand C | Cand D | Total | Rejected | NOTA | Tendered
-----------+--------+--------+--------+--------+-------+----------+------+---------
         1 |    243 |      8 |    136 |      0 |   735 |        0 |    6 |        0
         2 |    210 |     10 |    142 |      5 |   706 |        0 |    2 |        0
```

The columns after the serial number are:
- One column per candidate (in the order listed in the PDF header)
- Total valid votes
- Rejected votes (test votes; almost always 0)
- NOTA votes
- Tendered votes (almost always 0)

The `--cols` argument in `extract_form20_pdf.py` refers to the
**candidate column number**, counting from 1 (the first candidate).
It does NOT count the serial number, total, rejected, NOTA, or tendered
columns.

---

## Step-by-step: identifying columns for a new PDF

### Step 1 — Open the PDF and find the header row

The header row lists all candidates. In Delhi Form 20s, it typically
spans two or three lines because candidate names are long. Read carefully
to identify each candidate's full name and party affiliation.

ECI Form 20s do not print party names in the header — only candidate
names. You need to cross-reference with the ECI result page for the
constituency (results.eci.gov.in) to confirm which candidate belongs
to which party.

### Step 2 — Number the candidates left to right

Write down:
```
1. [Name] — [Party]
2. [Name] — [Party]
3. [Name] — [Party]
...
```

### Step 3 — Decide how to group candidates

You will typically want output columns for the main parties plus an
"others" column that sums all minor candidates and independents.

Example for GK 2013 (6 candidates):
```
1. Ajay Kumar Malhotra   — BJP
2. Mukesh Bhardwaj       — INC (rebel, unofficial)
3. Virender Kasana       — INC (official candidate)
4. Nanhey Khan Qureshi   — Independent
5. Saurabh Bharadwaj     — AAP
6. Ashok Kumar           — Independent
```

Desired output columns: bjp, inc, aap, others

Mapping:
- bjp    → col 1
- inc    → col 3  (official INC candidate only)
- aap    → col 5
- others → cols 2 + 4 + 6  (rebel INC + independents)

`--cols` argument: `1 3 5 246`
(the `246` token means sum columns 2, 4, and 6 into one output column)

### Step 4 — Verify using the footer totals

After running the extractor, compare the printed column totals against
the EVM-votes summary row at the bottom of the Form 20. These should
match exactly (within rounding).

The footer row is typically labelled "Total No. of votes recorded at
Polling Stations" or similar. It lists EVM totals per candidate.

If they do not match, the most common causes are:
- Wrong column number (off by one)
- A candidate column was split across two PDF columns due to formatting
- The PDF has a non-standard layout (some states format differently)

---

## Common layout variations

### Standard Delhi layout (most common in this repo)

6-8 candidates, clean typeset PDF, one candidate per column.
Works with the auto-detection in `extract_form20_pdf.py`.

### Scanned PDFs (older elections, some states)

OCR quality varies. If extraction produces garbage rows, the PDF may
need pre-processing with `ocrmypdf` before running the extractor:
```bash
ocrmypdf input.pdf input_ocr.pdf
python analysis/extract_form20_pdf.py input_ocr.pdf ...
```

### Many-candidate constituencies

Some constituencies have 20+ candidates. The table spans multiple PDF
columns or wraps across pages. In these cases `--n-candidates` must be
set manually and the `--cols` grouping becomes more important to get right.

### Bihar / UP layout

Rural state Form 20s often have more candidates and use a slightly
different column ordering. Always verify the header carefully.

---

## Quick reference: elections covered in this repo

| File | Year | AC | Candidates | Column mapping used |
|------|------|----|-----------|---------------------|
| delhi_2013_AC50_greater_kailash.pdf | 2013 | 50 | 6 | `--parties bjp inc aap others --cols 1 3 5 246` |
| delhi_2025_AC25_moti_nagar.pdf | 2025 | 25 | 8 | TBD — see extraction notes below |
| delhi_2025_AC01_nerela.pdf | 2025 | 1 | 5 | TBD — see extraction notes below |

### Moti Nagar 2025 (AC-25) candidates (from PDF header)

```
1. Avinash Gupta         — INC
2. Rajender Singh        — BJP (Shivcharan Goel)
3. Harish Khurana Bothra — AAP (Harish Khurana)
4. Mahesh Dubey          — IND
5. Vijay Kumar Sharma    — IND
6. Vishal Sahni          — IND
7. Gauri Shankar         — IND
8. Sadre Alam            — IND
9. Harish                — IND
```

Suggested mapping:
`--parties inc bjp aap others --cols 1 2 3 456789`

### Nerela 2025 (AC-01) candidates (from PDF header)

```
1. Aruna               — INC
2. Raj Karan Khatri    — BJP
3. Sharad Kumar        — AAP
4. Anil Kumar Singh    — IND
5. MD Khalid           — IND
6. Budiya              — IND
7. Vikas Bhardwaj      — IND
```

Suggested mapping:
`--parties inc bjp aap others --cols 1 2 3 4567`

---

## Adding a verified mapping to this file

When you successfully extract a new constituency, please add a row to
the quick reference table above and note the candidate list. This saves
the next contributor from repeating the identification work.
