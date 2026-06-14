# India Electoral Data Commons

Open-source tools for booth-level and constituency-level electoral analysis
using publicly available Election Commission of India (ECI) data.

Built for researchers, journalists, political scientists, election observers,
and civil society organisations who want to work with Indian electoral data
at the finest geographic unit available in public records — the individual
polling station — without relying on proprietary platforms or closed datasets.

All analysis uses only official government publications. No individual voter
data, personal information, or demographic inference is used anywhere in
this project.

---

## Why this exists

Indian election results are public but hard to use. ECI publishes Form 20
(booth-wise results) as scanned PDFs after every election. Candidate
affidavit data is published on myneta.info. Electoral rolls are published
by state CEO offices. Each source is individually accessible but connecting
them into usable analysis requires significant technical effort that most
civil society organisations, independent researchers, and small political
parties cannot easily manage.

This project lowers that barrier. Each script takes a public data source
as input and produces a clean CSV or printed analysis as output. Scripts
can be combined into pipelines or used independently.

---

## Repository structure

```
india-electoral-data-commons/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/
│   │   └── form20_pdfs/          # Original Form 20 PDFs from ECI/CEO portals
│   │       ├── delhi_2013_AC50_greater_kailash.pdf
│   │       ├── delhi_2025_AC25_moti_nagar.pdf
│   │       └── delhi_2025_AC01_nerela.pdf
│   └── processed/                # CSVs extracted from the above PDFs
│       └── delhi_2013_AC50_greater_kailash.csv
│
├── analysis/                     # Analysis scripts
│   ├── extract_form20_pdf.py
│   ├── booth_swing.py
│   ├── turnout_anomaly.py
│   ├── nota_analysis.py
│   └── vote_share_distortion.py
│
├── examples/                     # Synthetic data for demonstrating the pipeline
│   └── greater_kailash/
│       ├── 2020_form20_synthetic.csv
│       ├── 2025_form20_synthetic.csv
│       └── electors_synthetic.csv
│
└── docs/
    ├── data_sources.md           # Where to find each data type, state by state
    ├── column_mapping_guide.md   # How to identify candidate columns in any Form 20
    └── adding_a_constituency.md  # Step-by-step for contributors
```

---

## Quickstart

```bash
git clone https://github.com/joyboseroy/india-electoral-data-commons
cd india-electoral-data-commons
pip install -r requirements.txt

# Extract a Form 20 PDF to CSV
python analysis/extract_form20_pdf.py \
    data/raw/form20_pdfs/delhi_2013_AC50_greater_kailash.pdf \
    --out data/processed/delhi_2013_AC50_greater_kailash.csv \
    --parties bjp inc aap others \
    --cols 1 3 5 246

# Run NOTA analysis
python analysis/nota_analysis.py \
    data/processed/delhi_2013_AC50_greater_kailash.csv \
    --margin 3188

# Compute vote-to-seat distortion for Delhi 2025
python analysis/vote_share_distortion.py --summary \
    --votes "bjp:4567422,aap:4329708,inc:638133" \
    --seats "bjp:48,aap:22,inc:0" \
    --total-seats 70 \
    --label "Delhi Assembly 2025"
```

---

## What is implemented

### 1. Form 20 PDF extractor (`analysis/extract_form20_pdf.py`)

Extracts booth-wise candidate vote counts from ECI Form 20 PDFs into a
clean CSV. Tested against official ECI totals for Greater Kailash AC-50
(Delhi 2013) with exact match on all party columns.

**Input**: Form 20 PDF from results.eci.gov.in or state CEO portal
**Output**: CSV with one row per polling station, one column per party

```bash
python analysis/extract_form20_pdf.py \
    data/raw/form20_pdfs/delhi_2013_AC50_greater_kailash.pdf \
    --out data/processed/delhi_2013_AC50_greater_kailash.csv \
    --parties bjp inc aap others \
    --cols 1 3 5 246
```

The `--cols` argument maps candidate column positions (1-indexed) to
party names. Use combined digits such as `246` to sum columns 2, 4, and 6
into a single output column. See `docs/column_mapping_guide.md` for how
to identify the correct mapping for any PDF.

---

### 2. Booth-level swing calculator (`analysis/booth_swing.py`)

Computes vote share swing between two elections at the polling station
level. Identifies which specific localities within a constituency shifted
most between elections — far more actionable than constituency-level
aggregates.

**Input**: Two Form 20 CSVs for the same constituency, different years
**Output**: CSV ranked by swing for a chosen party, with turnout change

```bash
python analysis/booth_swing.py \
    data/processed/delhi_2020_AC50_greater_kailash.csv \
    data/processed/delhi_2025_AC50_greater_kailash.csv \
    --focus-party bjp --out swing_results.csv --top 10
```

**Note on delimitation**: Polling station part numbers can change between
elections if boundaries are redrawn. Always check whether a delimitation
occurred between the two elections you are comparing. See
`docs/adding_a_constituency.md` for guidance.

---

### 3. Turnout anomaly detector (`analysis/turnout_anomaly.py`)

Flags polling stations where turnout is statistically unusual — more than
N standard deviations above or below the constituency mean. High-turnout
outliers are one of the standard indicators used in election observation.
Low-turnout outliers may point to access issues or other local factors.

**Input**: Form 20 CSV + per-booth elector counts (or constituency total)
**Output**: CSV of flagged polling stations with z-scores and direction

```bash
# With per-booth elector counts (most accurate):
python analysis/turnout_anomaly.py \
    data/processed/delhi_2013_AC50_greater_kailash.csv \
    --electors data/processed/delhi_2013_AC50_electors.csv \
    --out anomalies.csv --threshold 2.0

# Approximate mode using only constituency-wide elector total:
python analysis/turnout_anomaly.py \
    data/processed/delhi_2013_AC50_greater_kailash.csv \
    --electors-total 143773 --out anomalies.csv
```

Per-booth elector counts are published annually by state CEO offices
as part of the electoral roll. See `docs/data_sources.md`.

---

### 4. NOTA concentration analysis (`analysis/nota_analysis.py`)

Ranks polling stations by NOTA (None of the Above) vote share and
computes constituency-wide statistics. If a winning margin is supplied,
reports whether total NOTA votes exceed the margin — an indicator of
how voter dissatisfaction compares to the closeness of the result.

**Input**: Form 20 CSV
**Output**: CSV ranked by NOTA share, printed summary

```bash
python analysis/nota_analysis.py \
    data/processed/delhi_2025_AC50_greater_kailash.csv \
    --margin 3188 --out nota_report.csv --top 15
```

---

### 5. Vote share vs seat share distortion (`analysis/vote_share_distortion.py`)

Computes the distortion between a party's vote share and its seat share
across a full state election. Calculates the Gallagher Index, a standard
political science measure of electoral disproportionality used widely in
comparative electoral systems research.

**Input**: Constituency-results CSV or summary totals on the command line
**Output**: Per-party distortion table, Gallagher Index, proportional
seat allocation for reference

```bash
python analysis/vote_share_distortion.py --summary \
    --votes "bjp:4567422,aap:4329708,inc:638133" \
    --seats "bjp:48,aap:22,inc:0" \
    --total-seats 70 \
    --label "Delhi Assembly 2025"
```

Sample output (Delhi 2025):

```
Party        Vote share   Seat share   Distortion
bjp              45.97%       68.57%      +22.60%  OVER-represented
aap              43.58%       31.43%      -12.15%  UNDER-represented
inc               6.42%        0.00%       -6.42%  UNDER-represented

Gallagher Index: 18.92  (Very high disproportionality)
Proportional allocation: BJP 32 seats, AAP 30, INC 4
```

Constituency-level results are published by ECI at results.eci.gov.in.

---

## What is not yet implemented

The following analyses are feasible from public data and are planned for
future development. Contributions are welcome on any of these.

### Candidate affidavit tracker
Every candidate files a Form 26 affidavit declaring assets, liabilities,
criminal cases, and educational qualifications. A scraper and comparison
tool could track asset growth across elections for the same candidate,
candidates with pending criminal cases by constituency, and other patterns.
**Data source**: myneta.info (structured), affidavit.eci.gov.in (PDFs).
**Complexity**: Medium.

### Candidate vote trajectory tracker
Tracks a candidate's personal vote share across multiple elections in the
same constituency, controlling for overall party performance. Useful for
identifying incumbents whose personal support is declining independently
of their party's trend.
**Data source**: ECI constituency results CSVs.
**Complexity**: Low — main challenge is candidate name normalisation
across election years.

### Delimitation change mapper
Maps old polling station part numbers to new ones across a delimitation
cycle, making `booth_swing.py` reliable across boundary change events.
**Data source**: Delimitation Commission of India order PDFs.
**Complexity**: High — delimitation PDFs are inconsistently formatted.

### Electoral roll change analysis
Compares registered elector counts per polling station between annual
roll revisions to surface unusual growth or decline in specific booths.
**Data source**: State CEO electoral roll PDFs (published annually).
**Complexity**: Medium.

### Grievance portal issue mapper
Scrapes and categorises public complaints from CPGRAMS and state
equivalents by district or constituency, producing a rough proxy for
civic issue concentration by area.
**Data source**: pgportal.gov.in and state equivalents.
**Complexity**: Medium — portal quality varies significantly by state.

### Alliance vote transfer estimator
Estimates how well vote transfer occurs in constituencies where alliance
partners ask voters to support each other, by comparing booth-level
results across similar constituencies with and without alliance
arrangements.
**Data source**: Form 20 CSVs across multiple constituencies.
**Complexity**: Medium — requires careful constituency selection.

### Postal ballot analysis
Extracts and compares postal ballot vote patterns from Form 20 summary
rows, which currently are excluded from the booth-level CSVs.
**Data source**: Form 20 PDFs (summary rows already present).
**Complexity**: Low — minor extension of `extract_form20_pdf.py`.

---

## Data sources

All data used in this project is publicly available from official sources.
See `docs/data_sources.md` for a full reference including URLs for each
state CEO portal, format notes, and reliability considerations.

Primary sources:
- **ECI results portal**: https://results.eci.gov.in (Form 20, results)
- **ECI affidavit portal**: https://affidavit.eci.gov.in (candidate declarations)
- **MyNeta**: https://myneta.info (structured affidavit aggregation)
- **State CEO portals**: electoral rolls, additional result documents
- **Delimitation Commission**: https://delimitationcommission.nic.in

---

## Contributing

See `docs/adding_a_constituency.md` for a complete walkthrough.

In brief:
- Add source PDFs to `data/raw/form20_pdfs/` using the naming convention
- Add extracted and verified CSVs to `data/processed/`
- Add candidate mapping notes to `docs/column_mapping_guide.md`
- Open a pull request with a brief description

Please do not add individual voter data, phone numbers, contact
information, or inferences based on personal attributes.

---

## License

MIT. Data files in `data/` are reproductions of public government
documents and carry no additional restrictions beyond their original
publication terms.
