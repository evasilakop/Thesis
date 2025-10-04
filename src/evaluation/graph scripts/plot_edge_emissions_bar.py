#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse, os

def parse_emissions(xml_file, metrics):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    rows = []
    for step in root.findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        sums = {m:0.0 for m in metrics}
        for veh in step.findall('vehicle'):
            for m in metrics:
                val = veh.get(m)
                if val: sums[m] += float(val)
        rows.append({'time': t, **sums})
    return pd.DataFrame(rows).sort_values('time')

def aggregate(df, bin_size):
    max_t = df['time'].max()
    bins = np.arange(0, max_t+bin_size, bin_size)
    df['bin'] = pd.cut(df['time'], bins, right=False)
    agg = df.groupby('bin').sum().reset_index()
    agg['time'] = [interval.left+bin_size/2 for interval in agg['bin']]
    return agg

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i','--input', nargs='+', required=True,
                   help='edgeEmissions XML files')
    p.add_argument('-l','--labels', nargs='+',
                   help='labels matching each input')
    p.add_argument('-b','--binsize', type=float, default=1.0,
                   help='bin width in seconds')
    p.add_argument('-o','--output', default='edge_emissions_bar.png',
                   help='output PNG file')
    args = p.parse_args()

    if args.labels and len(args.labels)!=len(args.input):
        p.error("labels and inputs must match in count")

    metrics = ['CO2','CO','HC','NOx','PMx','fuel']
    n_runs = len(args.input)
    width = args.binsize * 0.8 / n_runs

    fig, ax = plt.subplots(figsize=(10,5))
    for idx, xml in enumerate(args.input):
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        df = parse_emissions(xml, metrics)
        agg = aggregate(df, args.binsize)
        label = args.labels[idx] if args.labels else os.path.basename(xml)
        # Plot only CO2 here; replicate loop for other metrics if desired
        positions = agg['time'] + (idx - (n_runs-1)/2)*width
        ax.bar(positions, agg['CO2'], width=width, label=f"{label} CO₂")

    ax.set_xlabel('Time [s]')
    ax.set_ylabel('CO₂ per interval [mg]')
    ax.set_title('CO₂ Emissions Comparison (Bar Chart)')
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(args.output, dpi=300)
    print("Saved:", args.output)

if __name__=='__main__':
    main()
