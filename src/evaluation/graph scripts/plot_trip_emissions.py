#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

def load_tripinfos(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    records = []
    for trip in root.findall('tripinfo'):
        arr = float(trip.get('arrival'))
        em = trip.find('emissions')
        records.append({
            'time': arr,
            'CO2':   float(em.get('CO2_abs',   0.0)),
            'PMx':   float(em.get('PMx_abs',   0.0)),
            'NOx':   float(em.get('NOx_abs',   0.0)),
            'Fuel':  float(em.get('fuel_abs',  0.0)),
        })
    return pd.DataFrame(records)

def aggregate_emissions(df, bin_size):
    max_t = df['time'].max()
    bins = np.arange(0, max_t + bin_size, bin_size)
    labels = bins[:-1] + bin_size/2
    df['bin'] = pd.cut(df['time'], bins=bins, labels=labels, right=False)
    agg = df.groupby('bin')[['CO2','PMx','NOx','Fuel']].sum().reset_index()
    agg['bin'] = agg['bin'].astype(float)
    return agg

def main():
    p = argparse.ArgumentParser(
        description="Plot aggregated tripInfo emissions over time for multiple runs"
    )
    p.add_argument(
        '-i','--input', nargs='+', required=True,
        help='one or more tripInfos.xml files'
    )
    p.add_argument(
        '-l','--labels', nargs='+',
        help='labels for each input (same order)'
    )
    p.add_argument(
        '-b','--binsize', default=1.0, type=float,
        help='time bin size in seconds'
    )
    p.add_argument(
        '-o','--output', default='trip_emissions_comparison.png',
        help='output figure name'
    )
    args = p.parse_args()

    if args.labels and len(args.labels) != len(args.input):
        raise ValueError("Number of labels must match number of input files")

    plt.figure(figsize=(10,5))
    for idx, xml in enumerate(args.input):
        if not os.path.exists(xml):
            raise FileNotFoundError(f"Cannot find {xml}")
        df = load_tripinfos(xml)
        agg = aggregate_emissions(df, args.binsize)
        label = args.labels[idx] if args.labels else os.path.basename(xml)
        plt.plot(
            agg['bin'], agg['CO2'], label=f"{label} CO₂"
        )
        plt.plot(
            agg['bin'], agg['Fuel'], '--', label=f"{label} Fuel"
        )
        # add PMx and NOx as needed:
        plt.plot(
            agg['bin'], agg['PMx'], ':', label=f"{label} PMx"
        )
        plt.plot(
            agg['bin'], agg['NOx'], '-.', label=f"{label} NOₓ"
        )

    plt.xlabel('Time [s]')
    plt.ylabel('Emissions per interval [mg]')
    plt.title('Network Emissions Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    print(f"Saved comparison plot to {args.output}")

if __name__ == '__main__':
    main()