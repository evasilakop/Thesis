#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import argparse, os

def parse_edge_emissions(xml_file, metrics):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    records = []
    for step in root.findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        sums = {m: 0.0 for m in metrics}
        for veh in step.findall('vehicle'):
            for m in metrics:
                val = veh.get(m)
                if val is not None:
                    sums[m] += float(val)
        records.append({'time': t, **sums})
    df = pd.DataFrame(records).sort_values('time')
    return df

def main():
    p = argparse.ArgumentParser(
        description="Plot summed edge-emissions from multiple XMLs"
    )
    p.add_argument(
        '-i','--input', nargs='+', required=True,
        help='edgeEmissions XML files'
    )
    p.add_argument(
        '-l','--labels', nargs='+',
        help='labels matching each input file'
    )
    p.add_argument(
        '-m','--metrics', nargs='+',
        default=['CO2','CO','HC','NOx','PMx','fuel'],
        help='emission attributes to sum and plot'
    )
    p.add_argument(
        '-o','--output', default='edge_emissions_multi.png',
        help='PNG output filename'
    )
    args = p.parse_args()

    if args.labels and len(args.labels) != len(args.input):
        p.error("Number of labels must match number of input files")

    plt.figure(figsize=(10,5))
    for idx, xml in enumerate(args.input):
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        df = parse_edge_emissions(xml, args.metrics)
        label = args.labels[idx] if args.labels else os.path.basename(xml)
        for m in args.metrics:
            plt.plot(df['time'], df[m], label=f"{label}: {m}")

    plt.xlabel('Time [s]')
    plt.ylabel('Emissions per step [mg]')
    plt.title('Edge Emissions Comparison Over Time')
    plt.legend(ncol=2, fontsize='small')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    print(f"Saved comparison plot to {args.output}")

if __name__ == '__main__':
    main()
