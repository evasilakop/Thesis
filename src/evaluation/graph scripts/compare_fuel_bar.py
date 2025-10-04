#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse, os

def parse_fuel(xml_file, bin_size):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    rows = []
    for step in root.findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        # sum fuel for all vehicles this timestep
        fuel_sum = sum(float(v.get('fuel', 0.0)) for v in step.findall('vehicle'))
        rows.append({'time': t, 'fuel': fuel_sum})
    df = pd.DataFrame(rows).sort_values('time')
    # bin into intervals
    bins = np.arange(0, df['time'].max() + bin_size, bin_size)
    df['bin'] = pd.cut(df['time'], bins, right=False)
    agg = df.groupby('bin')['fuel'].sum().reset_index()
    agg['time'] = [interval.left + bin_size/2 for interval in agg['bin']]
    return agg[['time','fuel']]

def main():
    p = argparse.ArgumentParser(
        description="Bar chart of fuel consumption per interval"
    )
    p.add_argument('-i','--input', nargs=2, required=True,
                   help='two edge-emissions XML files')
    p.add_argument('-l','--labels', nargs=2, default=None,
                   help='labels for each file')
    p.add_argument('-b','--binsize', type=float, default=60.0,
                   help='interval width in seconds')
    p.add_argument('-o','--output', default='fuel_60s.png',
                   help='output PNG filename')
    args = p.parse_args()

    files = args.input
    labels = args.labels if args.labels else [os.path.basename(f) for f in files]

    # parse & bin
    dfs = []
    for xml in files:
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        dfs.append(parse_fuel(xml, args.binsize))

    # plot
    width = args.binsize * 0.8 / len(dfs)
    fig, ax = plt.subplots(figsize=(10,5))
    for idx, (df, lbl) in enumerate(zip(dfs, labels)):
        pos = df['time'] + (idx - (len(dfs)-1)/2) * width
        ax.bar(pos, df['fuel'], width=width, label=lbl)

    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Fuel consumption per interval [mg]')
    ax.set_title(f'Fuel Consumption Every {int(args.binsize)} s')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    print(f"Saved bar chart to {args.output}")

if __name__=='__main__':
    main()
