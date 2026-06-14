#!/usr/bin/env python3
"""
vote_share_distortion.py

Computes the distortion between a party's vote share and its seat share
across an election — a standard measure used in electoral systems analysis.

In first-past-the-post (FPTP) systems, a party can win a disproportionate
number of seats relative to its actual vote share. This script quantifies
that distortion for every party in an election, and computes the
Gallagher Index (a standard measure of overall electoral disproportionality
used in political science literature).

INPUT:
    A CSV with constituency-level results. Expected columns:
        constituency, total_votes, <party1>_votes, <party2>_votes, ...
        (one row per constituency, same format as booth_swing.py but
        with one row per constituency rather than per polling station)

    OR use --summary mode and pass totals directly on the command line.

USAGE:
    # From a constituency-results CSV:
    python vote_share_distortion.py results.csv \
        --seats bjp:48 aap:22 inc:0 \
        --total-seats 70

    # Quick summary mode (no CSV needed):
    python vote_share_distortion.py --summary \
        --votes  "bjp:2300000,aap:2100000,inc:350000" \
        --seats  "bjp:48,aap:22,inc:0" \
        --total-seats 70

OUTPUT:
    Table of vote share vs seat share per party, distortion in percentage
    points, and the Gallagher Index for the election.

GALLAGHER INDEX:
    LSq = sqrt(0.5 * sum((vote_share_i - seat_share_i)^2))
    Values above 10 indicate significant disproportionality.
    UK FPTP typically scores 15-20; PR systems typically score 1-5.

DATA SOURCE:
    Constituency-level results are available from results.eci.gov.in
    after each election. The ECI publishes these as CSV/Excel for
    state assembly elections.
"""

import argparse
import csv
import math
import sys


def parse_kv(s):
    """Parse 'bjp:48,aap:22,inc:0' into {'bjp': 48, 'aap': 22, 'inc': 0}"""
    result = {}
    for item in s.split(','):
        k, v = item.strip().split(':')
        result[k.strip()] = float(v.strip())
    return result


def gallagher_index(vote_shares, seat_shares):
    parties = set(vote_shares) | set(seat_shares)
    lsq = sum(
        (vote_shares.get(p, 0) - seat_shares.get(p, 0)) ** 2
        for p in parties
    )
    return math.sqrt(0.5 * lsq)


def print_table(rows, gallagher):
    col_w = 18
    header = (f"{'Party':<{col_w}}  {'Vote share':>11}  {'Seat share':>11}  "
              f"{'Distortion':>11}  {'Direction'}")
    print(header)
    print("-" * len(header))
    for r in sorted(rows, key=lambda x: -x['vote_share']):
        direction = ""
        d = r['distortion']
        if d > 0.5:
            direction = "OVER-represented"
        elif d < -0.5:
            direction = "UNDER-represented"
        else:
            direction = "~proportional"
        print(f"{r['party']:<{col_w}}  {r['vote_share']:>10.2f}%  "
              f"{r['seat_share']:>10.2f}%  {d:>+10.2f}%  {direction}")
    print("-" * len(header))
    print(f"\nGallagher Index (LSq): {gallagher:.2f}")
    if gallagher >= 15:
        level = "Very high disproportionality"
    elif gallagher >= 10:
        level = "High disproportionality"
    elif gallagher >= 5:
        level = "Moderate disproportionality"
    else:
        level = "Low disproportionality"
    print(f"Interpretation: {level}")
    print("(Reference: UK FPTP ~15-20, German PR ~2-4, India varies 10-20)")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("results_csv", nargs='?', default=None,
                    help="Constituency-results CSV (optional in --summary mode)")
    ap.add_argument("--summary", action="store_true",
                    help="Quick mode: pass vote and seat totals directly")
    ap.add_argument("--votes", default=None,
                    help="Vote totals per party: 'bjp:2300000,aap:2100000,...'")
    ap.add_argument("--seats", default=None,
                    help="Seats won per party: 'bjp:48,aap:22,inc:0,...'")
    ap.add_argument("--total-seats", type=int, required=True,
                    help="Total seats in the assembly")
    ap.add_argument("--label", default="Election",
                    help="Label for the output (e.g. 'Delhi 2025')")
    args = ap.parse_args()

    print(f"\n=== Vote Share vs Seat Share Distortion: {args.label} ===\n")

    # Get seat counts
    if not args.seats:
        sys.exit("--seats is required. Format: 'bjp:48,aap:22,inc:0'")
    seat_counts = parse_kv(args.seats)
    total_seats = args.total_seats
    seat_shares = {p: v / total_seats * 100 for p, v in seat_counts.items()}

    # Get vote totals
    if args.summary or not args.results_csv:
        if not args.votes:
            sys.exit("In --summary mode, --votes is required.")
        vote_counts = parse_kv(args.votes)
    else:
        # Load from CSV
        vote_counts = {}
        with open(args.results_csv) as f:
            reader = csv.DictReader(f)
            party_cols = [c for c in reader.fieldnames
                          if c.endswith('_votes') and c != 'total_votes']
            for row in reader:
                for col in party_cols:
                    party = col.replace('_votes', '')
                    vote_counts[party] = vote_counts.get(party, 0) + int(row[col])

    total_votes = sum(vote_counts.values())
    vote_shares = {p: v / total_votes * 100 for p, v in vote_counts.items()}

    # Build output rows
    all_parties = set(vote_shares) | set(seat_shares)
    rows = []
    for p in all_parties:
        vs = vote_shares.get(p, 0)
        ss = seat_shares.get(p, 0)
        rows.append({
            'party': p,
            'votes': vote_counts.get(p, 0),
            'vote_share': round(vs, 2),
            'seats': seat_counts.get(p, 0),
            'seat_share': round(ss, 2),
            'distortion': round(ss - vs, 2)
        })

    g_index = gallagher_index(vote_shares, seat_shares)

    print(f"Total votes counted : {total_votes:,}")
    print(f"Total seats         : {total_seats}")
    print()
    print_table(rows, g_index)

    # Proportional seats calculation
    print("\nFor reference — proportional seat allocation would give:")
    prop_header = f"  {'Party':<18}  {'Actual seats':>13}  {'Proportional seats':>19}  Difference"
    print(prop_header)
    for r in sorted(rows, key=lambda x: -x['vote_share']):
        prop = r['vote_share'] / 100 * total_seats
        diff = r['seats'] - prop
        print(f"  {r['party']:<18}  {int(r['seats']):>13}  {prop:>18.1f}  {diff:>+.1f}")


if __name__ == "__main__":
    main()
