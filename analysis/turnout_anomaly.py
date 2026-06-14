#!/usr/bin/env python3
"""
turnout_anomaly.py

Identifies polling stations with statistically unusual turnout within
a constituency, using Form 20 data combined with electoral roll elector
counts.

High turnout outliers (significantly above constituency mean) are a
standard signal used by election observers and returning officer
objection processes. Low turnout outliers may indicate access issues,
booth capture, or demographic patterns worth investigating on the ground.

This script does not make any claims about causes. It surfaces the
statistical pattern; ground knowledge is needed to interpret it.

INPUT:
    A Form 20 CSV (output of extract_form20_pdf.py), plus either:
    (a) a separate electors CSV with columns: part_no, electors
    (b) --electors-total N  (constituency-wide total, used to estimate
        per-booth electors as total_votes / mean_turnout — less precise
        but useful when per-booth elector data is unavailable)

USAGE:
    # With per-booth elector counts (most accurate):
    python turnout_anomaly.py form20.csv --electors electors.csv \
        --out anomalies.csv --threshold 2.0

    # With only constituency-wide elector total (approximate):
    python turnout_anomaly.py form20.csv --electors-total 185000 \
        --out anomalies.csv --threshold 2.0

    --threshold : number of standard deviations from mean to flag
                  as anomalous (default 2.0)

OUTPUT:
    CSV of flagged polling stations with turnout %, z-score, and flag
    direction (HIGH or LOW). Printed summary shows top outliers.

GETTING PER-BOOTH ELECTOR DATA:
    Electoral rolls are published by state CEO offices. The roll lists
    electors per part (polling station). CEO Delhi publishes these at:
    https://ceodelhi.gov.in/OnlineErms/DownloadElectoralRoll.aspx
    You can extract part_no and elector counts from the roll PDFs using
    a similar approach to extract_form20_pdf.py.
"""

import argparse
import csv
import sys
import math


def load_form20(path):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append({
                'part_no': int(row['part_no']),
                'total_votes': int(row['total_votes'])
            })
    return rows


def load_electors(path):
    electors = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            electors[int(row['part_no'])] = int(row['electors'])
    return electors


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
    ap.add_argument("--electors", default=None,
                    help="CSV with columns part_no,electors (per-booth elector counts)")
    ap.add_argument("--electors-total", type=int, default=None,
                    help="Constituency-wide total electors (approximate fallback)")
    ap.add_argument("--out", default="turnout_anomalies.csv", help="Output CSV path")
    ap.add_argument("--threshold", type=float, default=2.0,
                    help="Standard deviations from mean to flag as anomalous (default 2.0)")
    ap.add_argument("--top", type=int, default=10,
                    help="Number of top outliers to print (default 10)")
    args = ap.parse_args()

    if not args.electors and not args.electors_total:
        sys.exit("Provide either --electors <csv> or --electors-total <N>")

    booths = load_form20(args.form20_csv)

    if args.electors:
        elector_map = load_electors(args.electors)
    else:
        # Estimate: distribute electors proportionally to votes cast
        # (assumes roughly uniform turnout — imprecise but directionally useful)
        total_votes = sum(b['total_votes'] for b in booths)
        elector_map = {}
        for b in booths:
            # scale each booth's electors proportional to its votes
            estimated = round(b['total_votes'] / total_votes * args.electors_total)
            elector_map[b['part_no']] = max(estimated, 1)
        print("Note: per-booth elector counts estimated from constituency total. "
              "Results are approximate. Supply --electors <csv> for accuracy.")

    # Compute turnout per booth
    records = []
    for b in booths:
        part = b['part_no']
        electors = elector_map.get(part)
        if not electors:
            continue
        turnout_pct = b['total_votes'] / electors * 100
        records.append({
            'part_no': part,
            'votes_cast': b['total_votes'],
            'electors': electors,
            'turnout_pct': round(turnout_pct, 2)
        })

    if not records:
        sys.exit("No matching part_no values between form20 and electors data.")

    turnouts = [r['turnout_pct'] for r in records]
    mean_t, std_t = mean_std(turnouts)
    print(f"\nConstituency turnout: mean={mean_t:.1f}%  std={std_t:.1f}%  "
          f"n={len(records)} polling stations")
    print(f"Flagging stations >{args.threshold} std devs from mean\n")

    flagged = []
    for r in records:
        z = (r['turnout_pct'] - mean_t) / std_t if std_t > 0 else 0
        r['z_score'] = round(z, 2)
        r['flag'] = None
        if z > args.threshold:
            r['flag'] = 'HIGH'
            flagged.append(r)
        elif z < -args.threshold:
            r['flag'] = 'LOW'
            flagged.append(r)

    flagged.sort(key=lambda r: abs(r['z_score']), reverse=True)

    fieldnames = ['part_no', 'electors', 'votes_cast', 'turnout_pct', 'z_score', 'flag']
    with open(args.out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flagged)

    print(f"Flagged {len(flagged)} anomalous polling stations "
          f"(threshold ±{args.threshold} std devs) → {args.out}")

    if flagged:
        print(f"\nTop {min(args.top, len(flagged))} outliers:")
        header = f"{'Part':>6}  {'Electors':>9}  {'Votes':>7}  "
        header += f"{'Turnout%':>9}  {'Z-score':>8}  Flag"
        print(header)
        print("-" * len(header))
        for r in flagged[:args.top]:
            print(f"{r['part_no']:>6}  {r['electors']:>9,}  "
                  f"{r['votes_cast']:>7,}  {r['turnout_pct']:>8.1f}%  "
                  f"{r['z_score']:>8.2f}  {r['flag']}")

    high = [r for r in flagged if r['flag'] == 'HIGH']
    low  = [r for r in flagged if r['flag'] == 'LOW']
    print(f"\nSummary: {len(high)} HIGH-turnout outliers, {len(low)} LOW-turnout outliers")
    print("Interpret findings with local ground knowledge before drawing conclusions.")


if __name__ == "__main__":
    main()
