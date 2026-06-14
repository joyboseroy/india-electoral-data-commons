#!/usr/bin/env python3
"""
booth_swing.py

Computes booth-level (polling-station-level) vote share swing between
two elections from Form 20-style CSV files.

INPUT FORMAT (CSV):
    part_no,locality,<party1>_votes,<party2>_votes,...,total_votes

The script is party-agnostic: it reads every column ending in "_votes"
except "total_votes" as a party column, and computes:
    - vote share per party per polling station, for each election year
    - swing (percentage-point change) per party per polling station
    - turnout change per polling station

USAGE:
    python booth_swing.py ELECTION_A.csv ELECTION_B.csv \
        --focus-party bjp --out swing.csv --top 10

OUTPUT:
    A CSV ranked by swing (descending) for the focus party, plus a
    printed summary of the highest and lowest swing polling stations.
"""

import argparse
import sys
import pandas as pd


def load_election(path):
    df = pd.read_csv(path)
    party_cols = [c for c in df.columns if c.endswith("_votes") and c != "total_votes"]
    if not party_cols:
        sys.exit(f"No '*_votes' columns found in {path}")
    if "total_votes" not in df.columns:
        df["total_votes"] = df[party_cols].sum(axis=1)
    for c in party_cols:
        df[c.replace("_votes", "_share")] = (df[c] / df["total_votes"] * 100).round(2)
    return df, party_cols


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("old_csv", help="Earlier election Form 20 CSV")
    ap.add_argument("new_csv", help="Later election Form 20 CSV")
    ap.add_argument("--focus-party", default=None,
                    help="Party prefix (e.g. 'bjp') to rank polling stations by swing. "
                         "If omitted, ranks by total absolute swing across all parties.")
    ap.add_argument("--out", default="booth_swing.csv", help="Output CSV path")
    ap.add_argument("--top", type=int, default=5,
                    help="How many polling stations to print in each direction")
    args = ap.parse_args()

    old_df, old_parties = load_election(args.old_csv)
    new_df, new_parties = load_election(args.new_csv)

    common_parties = [p for p in old_parties if p in new_parties]
    if not common_parties:
        sys.exit("No common party columns between the two files. "
                 "Ensure column names match across election years.")

    merged = old_df.merge(
        new_df, on="part_no", suffixes=("_old", "_new"), how="inner"
    )
    if merged.empty:
        sys.exit("No matching part_no values between the two files. "
                 "Polling station numbers must align across elections.")

    for p in common_parties:
        old_share = p.replace("_votes", "_share") + "_old"
        new_share = p.replace("_votes", "_share") + "_new"
        merged[p.replace("_votes", "_swing")] = (
            merged[new_share] - merged[old_share]
        ).round(2)

    merged["turnout_old"] = merged["total_votes_old"]
    merged["turnout_new"] = merged["total_votes_new"]
    merged["turnout_change"] = merged["turnout_new"] - merged["turnout_old"]

    swing_cols = [p.replace("_votes", "_swing") for p in common_parties]

    if args.focus_party:
        focus_col = f"{args.focus_party}_swing"
        if focus_col not in merged.columns:
            sys.exit(f"--focus-party '{args.focus_party}' not found. "
                     f"Available: {[c.replace('_swing','') for c in swing_cols]}")
        merged = merged.sort_values(focus_col, ascending=False)
        rank_col = focus_col
    else:
        merged["total_abs_swing"] = merged[swing_cols].abs().sum(axis=1)
        merged = merged.sort_values("total_abs_swing", ascending=False)
        rank_col = "total_abs_swing"

    locality_col = "locality_old" if "locality_old" in merged.columns else None
    keep_cols = ["part_no"]
    if locality_col:
        keep_cols.append(locality_col)
    keep_cols += swing_cols + ["turnout_old", "turnout_new", "turnout_change", rank_col]
    keep_cols = list(dict.fromkeys(keep_cols))

    out_df = merged[keep_cols].copy()
    if locality_col:
        out_df = out_df.rename(columns={locality_col: "locality"})

    out_df.to_csv(args.out, index=False)
    print(f"Wrote {len(out_df)} polling station rows to {args.out}\n")

    print(f"Top {args.top} polling stations by '{rank_col}' (highest first):")
    print(out_df.head(args.top).to_string(index=False))

    print(f"\nBottom {args.top} polling stations by '{rank_col}' (lowest):")
    print(out_df.tail(args.top).to_string(index=False))

    if args.focus_party:
        print(f"\nConstituency-wide {args.focus_party.upper()} swing "
              f"(mean across polling stations): "
              f"{out_df[rank_col].mean():.2f} percentage points")


if __name__ == "__main__":
    main()
