import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse, os
from scipy.ndimage import uniform_filter1d

def parse_emissions(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    records = []
    for step in root.findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        co2 = sum(float(v.get('CO2', 0.0)) for v in step.findall('vehicle'))
        records.append({'time': t, 'CO2': co2})
    return pd.DataFrame(records).sort_values('time')

def bin_emissions(df, bin_size):
    bins = np.arange(0, df['time'].max() + bin_size, bin_size)
    df['bin'] = pd.cut(df['time'], bins, right=False)
    #agg = df.groupby('bin')['CO2'].sum().reset_index()
    #get mean
    agg = df.groupby('bin')['CO2'].mean().reset_index()
    agg['time'] = [interval.left + bin_size/2 for interval in agg['bin']]
    return agg[['time', 'CO2']]

def plot_with_smooth(dfs, labels, output):
    plt.figure(figsize=(10,5))
    for df, label in zip(dfs, labels):
        plt.scatter(df['time'], df['CO2'], alpha=0.6, label=f"{label} (raw)")
        smooth = uniform_filter1d(df['CO2'], size=3)
        plt.plot(df['time'], smooth, label=f"{label} (smoothed)", linewidth=2)

    plt.xlabel("Time [s]")
    plt.ylabel("CO₂ emissions per 60s [mg]")
    plt.title("CO₂ Emissions Over Time (Scatter + Smoothed Curve)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output, dpi=300)
    print(f"Saved to {output}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i','--input', nargs='+', required=True)
    p.add_argument('-l','--labels', nargs='+')
    p.add_argument('-b','--binsize', type=float, default=60.0)
    p.add_argument('-o','--output', default='co2_smoothed.png')
    args = p.parse_args()

    if args.labels and len(args.labels) != len(args.input):
        p.error("Labels must match number of input files")

    dfs = []
    for xml in args.input:
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        df_raw = parse_emissions(xml)
        df_binned = bin_emissions(df_raw, args.binsize)
        dfs.append(df_binned)

    labels = args.labels if args.labels else args.input
    plot_with_smooth(dfs, labels, args.output)

if __name__ == '__main__':
    main()
