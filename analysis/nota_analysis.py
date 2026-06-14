#!/usr/bin/env python3
"""
nota_analysis.py

Analyses NOTA (None of the Above) vote concentration across polling
stations in a constituency, and cross-references with winning margin
to identify priority areas for candidate improvement and outreach.

NOTA votes represent electors who turned out but rejected all candidates.
High NOTA concentration in a constituency with a narrow winning margin
is strategically significant: if a credible candidate had been available,
some of these voters might have voted differently.

This script:
    1. Ranks polling stations by NOTA share (highest first)
    2. Computes constituency-wide NOTA statistics
    3. If a winning margin is supplied, estimates how many NOTA votes
       exceed the margin (i.e. how many "persuadable" voters exist)
    4. Flags polling stations where NOTA share is above the
       constituency mean by a configurable threshold

INPUT:
    A Form 20 CSV (output of extract_form20_pdf.py).
    The CSV must include a nota_votes column.

USAGE:
    python nota_analysis.py form20.csv \
        --out nota_report.csv \
        --margin 3188 \
        --top 15

    --margin : winning margin in the constituency (optional).
               If supplied, the script reports total NOTA votes vs margin.
    --top    : number of highest-NOTA polling stations to print

OUTPUT:
    CSV of all polling stations ranked by NOTA share, plus printed summary.
"""

import argparse
import csv
import sys
import math


def mean_std(values):
    n = len(values)
    if n < 2:
        return 0, 0
    m = sum(values) / n
    variance = sum((v - m) ** 2 for v in values) / (n - 1)
    return m, math.sqrt(variance)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("form20_csv", help="Form 20 CSV (output of extract_form20_pdf.py)")
    ap.add_argument("--out", default="nota_analysis.csv", help="Output CSV path")
    ap.add_argument("--margin", type=int, default=None,
                    help="Winning margin in votes (for context against total NOTA)")
    ap.add_argument("--top", type=int, default=10,
                    help="Number of highest-NOTA polling stations to print")
    ap.add_argument("--threshold", type=float, default=1.5,
                    help="Std devs above mean NOTA share to flag as high-NOTA "
                         "(default 1.5)")
    args = ap.parse_args()

    rows = []
    with open(args.form20_csv) as f:
        reader = csv.DictReader(f)
        if 'nota_votes' not in reader.fieldnames:
            sys.exit("CSV does not contain a 'nota_votes' column. "
                     "Re-extract from Form 20 PDF using extract_form20_pdf.py.")
        for row in reader:
            total = int(row['total_votes'])
            nota  = int(row['nota_votes'])
            if total > 0:
                rows.append({
                    'part_no':    int(row['part_no']),
                    'total_votes': total,
                    'nota_votes':  nota,
                    'nota_share':  round(nota / total * 100, 2)
                })

    if not rows:
        sys.exit("No valid rows found in the CSV.")

    rows.sort(key=lambda r: r['nota_share'], reverse=True)

    nota_shares = [r['nota_share'] for r in rows]
    mean_n, std_n = mean_std(nota_shares)
    total_nota = sum(r['nota_votes'] for r in rows)
    total_votes = sum(r['total_votes'] for r in rows)
    overall_nota_pct = total_nota / total_votes * 100

    threshold_pct = mean_n + args.threshold * std_n

    for r in rows:
        r['above_mean'] = round(r['nota_share'] - mean_n, 2)
        r['flag'] = 'HIGH' if r['nota_share'] >= threshold_pct else ''

    fieldnames = ['part_no', 'total_votes', 'nota_votes',
                  'nota_share', 'above_mean', 'flag']
    with open(args.out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nNOTA Analysis — {len(rows)} polling stations")
    print(f"  Total NOTA votes   : {total_nota:,}")
    print(f"  Total votes cast   : {total_votes:,}")
    print(f"  Overall NOTA share : {overall_nota_pct:.2f}%")
    print(f"  Mean NOTA per booth: {mean_n:.2f}%  (std {std_n:.2f}%)")
    print(f"  High-NOTA threshold: >{threshold_pct:.2f}% "
          f"(mean + {args.threshold} std devs)")

    high_nota = [r for r in rows if r['flag'] == 'HIGH']
    print(f"  Flagged HIGH-NOTA  : {len(high_nota)} polling stations")

    if args.margin is not None:
        print(f"\n  Winning margin     : {args.margin:,} votes")
        print(f"  Total NOTA votes   : {total_nota:,} votes")
        if total_nota > args.margin:
            print(f"  NOTA exceeds margin by {total_nota - args.margin:,} votes.")
            print(f"  This means voter dissatisfaction with all candidates "
                  f"exceeds the margin of victory.")
            print(f"  A stronger candidate could potentially convert some of "
                  f"these into active votes.")
        else:
            print(f"  NOTA is below the winning margin "
                  f"({args.margin - total_nota:,} votes short).")

    print(f"\nTop {min(args.top, len(rows))} polling stations by NOTA share:")
    header = f"{'Part':>6}  {'Votes':>7}  {'NOTA':>6}  {'NOTA%':>7}  {'vs Mean':>8}  Flag"
    print(header)
    print("-" * len(header))
    for r in rows[:args.top]:
        print(f"{r['part_no']:>6}  {r['total_votes']:>7,}  "
              f"{r['nota_votes']:>6,}  {r['nota_share']:>6.2f}%  "
              f"{r['above_mean']:>+7.2f}%  {r['flag']}")

    print(f"\nFull results written to: {args.out}")


if __name__ == "__main__":
    main()
