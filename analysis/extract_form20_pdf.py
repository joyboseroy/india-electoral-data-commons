#!/usr/bin/env python3
"""
extract_form20_pdf.py

Extracts booth-wise vote data from ECI Form 20 PDFs into a CSV
compatible with booth_swing.py.

Form 20 ("Final Result Sheet") is the official document published by
Returning Officers after each election, listing candidate-wise votes
for every polling station in a constituency.

USAGE:
    python extract_form20_pdf.py INPUT.pdf \
        --out OUTPUT.csv \
        --parties bjp inc aap others \
        --cols   1   3   5   246

    --parties : short names for output CSV columns, one per group
    --cols    : which candidate column(s) to map to each party name
                (1-indexed, counting from the first candidate column).
                Use combined digits (e.g. '246') to sum columns 2, 4,
                and 6 into a single output column.

FORM 20 COLUMN STRUCTURE (typical Delhi format):
    booth_no | cand_1 | cand_2 | ... | cand_N | total | rejected | NOTA | tendered

    Column numbers in --cols are 1-indexed from cand_1.

IDENTIFYING COLUMN ORDER:
    Open the PDF and read the candidate header row. Note which position
    (left to right) each candidate occupies. Map these positions to the
    party names you want in the output.

WORKED EXAMPLE — Greater Kailash AC-50, Delhi 2013:
    Candidates in PDF order:
        1. Ajay Kumar Malhotra (BJP)
        2. Mukesh Bhardwaj (INC — rebel/independent)
        3. Virender Kasana (INC — official)
        4. Nanhey Khan Qureshi (Independent)
        5. Saurabh Bharadwaj (AAP)
        6. Ashok Kumar (Independent)

    Command:
        python extract_form20_pdf.py \\
            data/raw/form20_pdfs/delhi_2013_AC50_greater_kailash.pdf \\
            --out data/processed/delhi_2013_AC50_greater_kailash.csv \\
            --parties bjp inc aap others \\
            --cols 1 3 5 246

    This maps col 1 → bjp, col 3 → inc (official), col 5 → aap,
    and sums cols 2+4+6 → others.

VERIFICATION:
    After extraction the script prints per-party totals. Compare these
    against the EVM-votes summary row in the Form 20 PDF footer to confirm
    the column mapping is correct before using the output.
"""

import argparse
import csv
import re
import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("Install pdfplumber first: pip install pdfplumber")


def parse_cols_arg(cols_tokens):
    """
    Parse the --cols argument into groups of column indices.
    '1 3 5 246' -> [[1], [3], [5], [2,4,6]]
    Multi-digit tokens like '246' mean sum columns 2, 4, 6.
    """
    result = []
    for token in cols_tokens:
        if len(token) > 1 and all(c.isdigit() for c in token):
            result.append([int(c) for c in token])
        else:
            result.append([int(token)])
    return result


def extract_booths(pdf_path, n_candidates):
    """
    Extract all polling-station rows from the PDF.
    Returns a list of integer lists:
        [part_no, cand1, cand2, ..., candN, total, rejected, nota, tendered]
    """
    expected_cols = 1 + n_candidates + 4
    pattern = r'^(\d+)' + r'\s+(\d+)' * (expected_cols - 1) + r'$'

    rows = []
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                m = re.match(pattern, line.strip())
                if m:
                    vals = [int(x) for x in m.groups()]
                    part_no = vals[0]
                    if part_no not in seen:
                        seen.add(part_no)
                        rows.append(vals)

    return sorted(rows, key=lambda r: r[0])


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("pdf", help="Form 20 PDF path")
    ap.add_argument("--out", default="form20_extracted.csv", help="Output CSV path")
    ap.add_argument("--parties", nargs="+", required=True,
                    help="Output column names, one per --cols group")
    ap.add_argument("--cols", nargs="+", required=True,
                    help="Candidate column numbers to map to each party name. "
                         "Use combined digits (e.g. '246') to sum cols 2, 4, 6.")
    ap.add_argument("--n-candidates", type=int, default=None,
                    help="Total number of candidates in the PDF. "
                         "Auto-detected if omitted; use this flag if auto-detection fails.")
    args = ap.parse_args()

    col_groups = parse_cols_arg(args.cols)

    if len(col_groups) != len(args.parties):
        sys.exit(f"--parties has {len(args.parties)} names "
                 f"but --cols has {len(col_groups)} groups. These must match.")

    # Auto-detect number of candidates
    n_cands = args.n_candidates
    rows = []
    if n_cands is None:
        for n in range(4, 21):
            rows = extract_booths(args.pdf, n)
            if len(rows) > 10:
                n_cands = n
                break
        if not rows:
            sys.exit("Could not auto-detect number of candidates. "
                     "Try --n-candidates with a value between 4 and 20.")
        print(f"Auto-detected {n_cands} candidates, {len(rows)} polling stations found")
    else:
        rows = extract_booths(args.pdf, n_cands)
        print(f"Extracted {len(rows)} polling stations ({n_cands} candidates)")

    fieldnames = (
        ['part_no']
        + [f"{p}_votes" for p in args.parties]
        + ['nota_votes', 'total_votes']
    )

    with open(args.out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            cand_vals = row[1:n_cands + 1]
            total = row[n_cands + 1]
            nota  = row[n_cands + 3]

            out_row = {'part_no': row[0], 'nota_votes': nota, 'total_votes': total}
            for party, col_group in zip(args.parties, col_groups):
                out_row[f"{party}_votes"] = sum(cand_vals[c - 1] for c in col_group)
            writer.writerow(out_row)

    print(f"Wrote: {args.out}")
    print("\nColumn totals (EVM votes only — postal votes appear separately in Form 20):")

    with open(args.out) as f:
        reader = csv.DictReader(f)
        totals = {}
        for row in reader:
            for k, v in row.items():
                if k != 'part_no':
                    totals[k] = totals.get(k, 0) + int(v)
    for k, v in totals.items():
        print(f"  {k}: {v:,}")

    print("\nVerify these totals against the EVM-votes row in the Form 20 PDF footer.")


if __name__ == "__main__":
    main()
