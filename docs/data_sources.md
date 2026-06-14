# Data Sources

This document lists the primary public data sources used in this project,
how to access them, and what each contains. All sources are official
government publications or publicly funded aggregators.

---

## 1. Form 20 — Booth-wise Final Result Sheet

**What it is**: The official booth-level result document published by the
Returning Officer after every election. Lists votes received by each
candidate at every polling station in a constituency.

**Who publishes it**: Election Commission of India (ECI) / state Chief
Electoral Officers (CEOs)

**Where to find it**:
- National results portal: https://results.eci.gov.in
  - Navigate to the relevant election year and state
  - Click a constituency name to reach its result page
  - The Form 20 PDF is linked from the constituency result page
- Delhi: https://ceodelhi.gov.in
- Maharashtra: https://ceo.maharashtra.gov.in
- Tamil Nadu: https://www.elections.tn.gov.in
- Kerala: https://www.ceo.kerala.gov.in
- West Bengal: https://ceowestbengal.nic.in
- Karnataka: https://ceo.karnataka.gov.in
- Uttar Pradesh: https://ceouttarpradesh.nic.in

**Format**: Scanned or typeset PDF, one file per constituency per election.
Table structure: one row per polling station, one column per candidate,
plus total / rejected / NOTA / tendered columns.

**How to use in this project**: Run `analysis/extract_form20_pdf.py`
to convert to CSV. See `docs/column_mapping_guide.md` for how to identify
the correct column order for your PDF.

**Naming convention used in this repo**:
`{state}_{year}_AC{number}_{constituency_name}.pdf`
Example: `delhi_2013_AC50_greater_kailash.pdf`

---

## 2. Constituency-level Results

**What it is**: Candidate-wise totals at the constituency level (not
booth-level). Useful for vote share distortion analysis and candidate
trajectory tracking.

**Where to find it**:
- https://results.eci.gov.in — HTML tables, scrapeable
- ECI also releases structured data files (Excel/CSV) for some elections
  via their open data initiative
- MyNeta (see below) aggregates these for all elections since 1977

**Format**: HTML tables on the ECI portal; Excel for some recent elections.

---

## 3. Candidate Affidavits (Form 26)

**What it is**: Self-declared information filed by every candidate before
an election: assets and liabilities, pending criminal cases, educational
qualifications, PAN number. Mandatory under Supreme Court order.

**Where to find it**:
- ECI affidavit portal: https://affidavit.eci.gov.in
  (search by election, state, constituency, or candidate name)
- MyNeta: https://myneta.info
  (aggregates affidavit data in a more structured, searchable format;
  covers elections from 2004 onwards with reasonable completeness)
- Association for Democratic Reforms (ADR): https://adrindia.org
  (publishes analysis of affidavit data; useful for methodology reference)

**Format**: PDF (ECI); structured HTML with some CSV exports (MyNeta).

**Notes**: Candidate names are not normalised across elections, making
multi-election tracking require fuzzy matching. MyNeta's structured
format is easier to work with than raw ECI PDFs for this purpose.

---

## 4. Electoral Rolls (Elector Counts per Polling Station)

**What it is**: The official list of registered voters. The summary pages
of the electoral roll list the number of registered electors per polling
station (part), broken down by gender. This is needed for turnout
calculation at the booth level.

**Where to find it**: State CEO portals publish electoral rolls annually.
They are typically available as downloadable PDFs by assembly constituency.
- Delhi: https://ceodelhi.gov.in/OnlineErms/DownloadElectoralRoll.aspx
- Most state CEO portals have a similar "Download Electoral Roll" section

**Format**: Multi-part PDFs (one per constituency). Summary pages list
part number, polling station name, and elector count. Detailed pages list
individual voters (not used in this project).

**Notes**: Rolls are revised multiple times per year (summary revision,
special summary revision). Use the final roll published before the
election date for turnout calculations.

---

## 5. Delimitation Orders

**What it is**: Official orders that redraw constituency boundaries and
reassign polling stations to constituencies. When delimitation occurs,
polling station part numbers change, making cross-election comparison
unreliable without a mapping.

**Where to find it**:
- Delimitation Commission of India: https://delimitationcommission.nic.in
- ECI also publishes the orders: https://eci.gov.in/delimitation/

**Format**: PDF. Tables map old to new part numbers and constituency
assignments.

**Notes**: The last major delimitation for state assemblies was 2008.
Some states have had partial revisions since. Always check whether a
delimitation occurred between the two elections you are comparing before
running `analysis/booth_swing.py`.

---

## 6. Grievance Portal Data

**What it is**: Public complaints filed by citizens to government through
online portals. Useful as a proxy for civic issue mapping by region.

**Where to find it**:
- Central: https://pgportal.gov.in (CPGRAMS)
- Delhi: https://edistrict.delhigovt.nic.in
- Most states have equivalents; quality and openness varies significantly

**Format**: HTML; some portals have structured exports, most require
scraping.

**Notes**: Grievance data is not available at polling-station level;
typically district or ward level at finest granularity. Useful for
constituency-level issue mapping rather than booth-level analysis.

---

## 7. ECI Open Data

**What it is**: ECI has published some structured election data as part
of open government initiatives.

**Where to find it**: https://eci.gov.in/statistical-report/
Statistical reports going back several decades, including voter turnout,
candidate data, and results in PDF and some Excel formats.

---

## Notes on data reliability

- Form 20 is the most reliable source: it is a signed legal document.
  Any discrepancy between Form 20 figures and other sources should be
  resolved in favour of Form 20.
- Affidavit data is self-declared and unverified by ECI. ADR and MyNeta
  have documented cases of underreporting.
- Grievance portal data reflects only complaints formally filed online,
  which skews toward urban and digitally connected populations.
- Electoral roll figures change between revision cycles; always note
  which revision you are using for turnout calculations.
