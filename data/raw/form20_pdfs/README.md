# Form 20 PDFs

Original, unmodified Form 20 PDFs sourced from ECI/CEO portals.

## Naming convention

{state}_{year}_AC{number}_{constituency_name}.pdf

Examples:
- delhi_2013_AC50_greater_kailash.pdf
- kerala_2021_AC140_thiruvananthapuram.pdf
- westbengal_2021_AC001_singur.pdf

## Files in this folder

| File | Source | Verified |
|------|--------|---------|
| delhi_2013_AC50_greater_kailash.pdf | results.eci.gov.in | Yes — extracted CSV totals match ECI figures exactly |
| delhi_2025_AC25_moti_nagar.pdf | results.eci.gov.in | Pending extraction |
| delhi_2025_AC01_nerela.pdf | results.eci.gov.in | Pending extraction |

## Adding a new file

See docs/adding_a_constituency.md for the full process.
After adding a PDF, update the table above with source URL and
verification status once you have run extract_form20_pdf.py and
confirmed the totals.
