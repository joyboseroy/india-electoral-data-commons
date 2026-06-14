# Adding a New Constituency

This guide walks through the complete process of adding booth-level
data for a new constituency to this repository, from finding the raw
PDF to running analysis and contributing back.

No programming experience is required for steps 1-3. Steps 4-7 require
running Python scripts from the command line.

---

## Step 1 — Find the Form 20 PDF

Go to https://results.eci.gov.in and navigate to:
- The election year you want
- Your state
- Your constituency

Look for a link to the "Final Result Sheet" or "Form 20". Download the PDF.

If the PDF is not on the ECI portal (older elections sometimes are not),
try your state Chief Electoral Officer (CEO) website. URLs for major
state CEO portals are listed in `docs/data_sources.md`.

---

## Step 2 — Name the file correctly

Rename the PDF following this convention:

```
{state}_{year}_AC{number}_{constituency_name}.pdf
```

Examples:
```
delhi_2025_AC50_greater_kailash.pdf
kerala_2021_AC140_thiruvananthapuram.pdf
westbengal_2021_AC001_singur.pdf
```

- Use lowercase, underscores only (no spaces or hyphens)
- Use the two-digit or three-digit AC number as printed on the Form 20
- For state names with spaces use no separator: `westbengal`, `tamilnadu`,
  `uttarpradesh`, `madhyapradesh`

Place the renamed PDF in:
```
data/raw/form20_pdfs/
```

---

## Step 3 — Identify candidate columns

Open the PDF and read the header row carefully. List all candidates in
left-to-right order as they appear in the table. Cross-reference with
the ECI result page (results.eci.gov.in) to confirm party affiliations —
Form 20 does not print party names, only candidate names.

See `docs/column_mapping_guide.md` for detailed instructions and examples.

---

## Step 4 — Install dependencies (first time only)

```bash
pip install -r requirements.txt
```

---

## Step 5 — Extract the PDF to CSV

```bash
python analysis/extract_form20_pdf.py \
    data/raw/form20_pdfs/YOUR_FILE.pdf \
    --out data/processed/YOUR_FILE.csv \
    --parties bjp inc aap others \
    --cols 1 3 5 246
```

Adjust `--parties` and `--cols` to match your candidate list from Step 3.

The script will print column totals after extraction. **Verify these
against the EVM-votes summary row in the Form 20 PDF footer before
proceeding.** If they do not match, recheck your `--cols` mapping.

---

## Step 6 — Run analysis

Once you have a verified CSV, run any combination of the analysis scripts:

```bash
# Booth-level swing (requires a second CSV for the same constituency)
python analysis/booth_swing.py \
    data/processed/EARLIER_ELECTION.csv \
    data/processed/LATER_ELECTION.csv \
    --focus-party bjp --out results/swing.csv

# NOTA analysis
python analysis/nota_analysis.py \
    data/processed/YOUR_FILE.csv \
    --margin 3188 --out results/nota.csv

# Turnout anomalies (needs elector counts — see data_sources.md)
python analysis/turnout_anomaly.py \
    data/processed/YOUR_FILE.csv \
    --electors data/processed/YOUR_ELECTORS.csv \
    --out results/turnout.csv

# Vote share vs seat share (state-level, not constituency-level)
python analysis/vote_share_distortion.py \
    --summary \
    --votes "bjp:NNNN,inc:NNNN,aap:NNNN" \
    --seats "bjp:N,inc:N,aap:N" \
    --total-seats N \
    --label "Your Election Label"
```

---

## Step 7 — Contribute back (optional but encouraged)

If you would like to add your constituency data to the shared repository:

1. Fork this repository on GitHub
2. Add your PDF to `data/raw/form20_pdfs/`
3. Add your extracted CSV to `data/processed/`
4. Add a row to the quick reference table in `docs/column_mapping_guide.md`
   with the candidate list and `--cols` mapping you used
5. Open a pull request with a brief description of the constituency and
   election year

**Please do not add**:
- Individual voter data of any kind
- Phone numbers or contact information
- Data that is not from official public government sources
- Inferences about individual voters based on name, address, or other
  personal attributes

---

## Troubleshooting

**"No rows extracted" or very few rows**

The PDF may be scanned (image-only) rather than typeset. Try running
OCR first:
```bash
pip install ocrmypdf
ocrmypdf input.pdf input_ocr.pdf
python analysis/extract_form20_pdf.py input_ocr.pdf ...
```

**Extracted totals do not match PDF footer**

Column mapping is wrong. The most common error is being off by one on
the column numbers. Re-read the PDF header carefully and recount.
See `docs/column_mapping_guide.md`.

**Part numbers do not align between two elections**

A delimitation or polling station renumbering may have occurred between
the two elections. Check the Delimitation Commission records
(delimitationcommission.nic.in) for your state and election years.
See the "Delimitation change mapper" section in the main README for
context on this known limitation.

**Script crashes on a particular page**

Some Form 20 PDFs have inconsistent formatting across pages (especially
older scanned documents). Open an issue on GitHub with the PDF name and
page number, and we will look at extending the extractor to handle it.
