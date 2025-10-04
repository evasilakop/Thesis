#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import argparse
import os

def count_stops(xml_file):
    """
    Parses an fcd-stop XML and returns a dict:
      time_step (float) → stopped_count (int)
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    counts = {}
    for step in root.findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        n = len(step.findall('vehicle'))
        counts[t] = n
    return counts

def main():
    p = argparse.ArgumentParser(
        description="Compare stopped-vehicle counts from two fcd-stop files"
    )
    p.add_argument(
        '-i','--inputs', nargs=2, required=True,
        help="Two fcd-stop XML files, e.g. fcd_stops_A.xml fcd_stops_B.xml"
    )
    p.add_argument(
        '-l','--labels', nargs=2, default=None,
        help="Optional labels for each file"
    )
    args = p.parse_args()

    files = args.inputs
    labels = args.labels if args.labels else [os.path.basename(f) for f in files]

    # Load counts
    data = {}
    for fname, lbl in zip(files, labels):
        if not os.path.isfile(fname):
            p.error(f"File not found: {fname}")
        data[lbl] = count_stops(fname)

    # Build a DataFrame keyed on sorted time steps
    times = sorted(set().union(*[d.keys() for d in data.values()]))
    df = pd.DataFrame(
        {lbl: [data[lbl].get(t, 0) for t in times] for lbl in labels},
        index=times
    )
    df.index.name = 'Time [s]'
    
    out_csv = "stopped_counts.csv"
    df.to_csv(out_csv, index=True)
    print(f"Saved stopped-vehicle counts to {out_csv}")

if __name__ == '__main__':
    main()