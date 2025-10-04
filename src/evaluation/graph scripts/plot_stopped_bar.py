#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse, os

def parse_summary(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    recs = []
    for step in root.findall('step'):
        t = float(step.get('time', step.get('begin', 0.0)))
        stopped = float(step.get('stopped', 0.0))
        recs.append({'time': t, 'stopped': stopped})
    return pd.DataFrame(recs).sort_values('time')

def bin_mean(df, bin_size):
    max_t = df['time'].max()
    bins = np.arange(0, max_t + bin_size, bin_size)
    df['bin'] = pd.cut(df['time'], bins, right=False)
    agg = df.groupby('bin')['stopped'].mean().reset_index()
    agg['time'] = [interval.left + bin_size/2 for interval in agg['bin']]
    return agg[['time','stopped']]

def main():
    p = argparse.ArgumentParser(
        description="Bar chart of mean stopped vehicles per interval"
    )
    p.add_argument(
        '-i','--input', nargs='+', required=True,
        help='summary XML files (one or more)'
    )
    p.add_argument(
        '-l','--labels', nargs='+',
        help='labels for each input (same order)'
    )
    p.add_argument(
        '-b','--binsize', type=float, default=60.0,
        help='interval width in seconds (default: 60)'
    )
    p.add_argument(
        '-o','--output', default='stopped_mean_bar.png',
        help='output PNG filename'
    )
    args = p.parse_args()

    if args.labels and len(args.labels) != len(args.input):
        p.error("Number of labels must match number of input files")

    # Parse and bin each run
    dfs = []
    for xml in args.input:
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        df = parse_summary(xml)
        binned = bin_mean(df, args.binsize)
        dfs.append(binned)

    labels = args.labels if args.labels else [os.path.basename(f) for f in args.input]
    n_runs = len(dfs)
    width = args.binsize * 0.8 / n_runs

    # Plot grouped bars
    fig, ax = plt.subplots(figsize=(10,5))
    for idx, (df, lbl) in enumerate(zip(dfs, labels)):
        positions = df['time'] + (idx - (n_runs-1)/2)*width
        ax.bar(positions, df['stopped'], width=width, label=lbl)

    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Mean stopped vehicles per interval')
    ax.set_title(f'Mean Stopped Vehicles Every {int(args.binsize)} s')
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(args.output, dpi=300)
    print(f"Saved bar chart to {args.output}")

if __name__ == '__main__':
    main()