#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse, os
from scipy.ndimage import uniform_filter1d

def parse_emissions(xml_file, metrics):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    records = []
    for step in root.findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        sums = {m: 0.0 for m in metrics}
        for v in step.findall('vehicle'):
            for m in metrics:
                val = v.get(m)
                if val:
                    sums[m] += float(val)
        sums['time'] = t
        records.append(sums)
    return pd.DataFrame(records).sort_values('time')

def bin_emissions(df, bin_size, metrics):
    max_t = df['time'].max()
    bins = np.arange(0, max_t + bin_size, bin_size)
    df['bin'] = pd.cut(df['time'], bins, right=False)
    agg = df.groupby('bin')[metrics].sum().reset_index()
    agg['time'] = [interval.left + bin_size/2 for interval in agg['bin']]
    return agg[['time'] + metrics]

def main():
    p = argparse.ArgumentParser(
        description="Scatter + smoothed curve for edge-emission metrics"
    )
    p.add_argument(
        '-i','--input', nargs='+', required=True,
        help='one or more edgeEmissions XML files'
    )
    p.add_argument(
        '-l','--labels', nargs='+',
        help='labels for each input (in same order)'
    )
    p.add_argument(
        '-m','--metrics', nargs='+', required=True,
        help='which attributes to plot, e.g. CO2 NOx PMx'
    )
    p.add_argument(
        '-b','--binsize', type=float, default=60.0,
        help='aggregation interval in seconds'
    )
    p.add_argument(
        '-o','--output', default='emissions_smooth.png',
        help='output PNG filename'
    )
    args = p.parse_args()

    if args.labels and len(args.labels) != len(args.input):
        p.error("Number of labels must match number of input files")

    # parse & bin each run
    dfs = []
    for xml in args.input:
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        raw = parse_emissions(xml, args.metrics)
        binned = bin_emissions(raw, args.binsize, args.metrics)
        dfs.append(binned)

    labels = args.labels if args.labels else args.input

    # plot each metric in its own subplot
    n = len(args.metrics)
    fig, axes = plt.subplots(n, 1, figsize=(10, 4*n), sharex=True)
    if n == 1:
        axes = [axes]

    for idx, metric in enumerate(args.metrics):
        ax = axes[idx]
        for df, lbl in zip(dfs, labels):
            ax.scatter(df['time'], df[metric],
                       alpha=0.6, label=f"{lbl} raw", s=20)
            smooth = uniform_filter1d(df[metric], size=3, mode='nearest')
            ax.plot(df['time'], smooth,
                    linewidth=2, label=f"{lbl} smoothed")
        ax.set_ylabel(f"{metric} [mg]")
        ax.set_title(f"{metric} emissions per {int(args.binsize)} s")
        ax.grid(True)
        ax.legend(fontsize='small')

    axes[-1].set_xlabel("Time [s]")
    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    print(f"Saved comparison plot to {args.output}")

if __name__ == '__main__':
    main()
