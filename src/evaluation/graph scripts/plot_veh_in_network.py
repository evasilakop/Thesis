import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse, os

def parse_running(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    for step in root.findall('step'):
        t = float(step.get('time', step.get('begin', 0.0)))
        running = float(step.get('running', 0))
        data.append({'time': t, 'running': running})
    return pd.DataFrame(data).sort_values('time')

def bin_and_agg(df, bin_size):
    # 1) turn the 'time' column into a TimedeltaIndex
    df.index = pd.to_timedelta(df['time'], unit='s')
    df.index.name = 'time'                            # name the index

    # 2) resample & take the mean of 'running'
    res = df['running'].resample(f'{int(bin_size)}s').mean()

    # 3) bring the index back into a column called 'time'
    res = res.reset_index()                           # now has columns ['time','running']

    # 4) convert from Timedelta to float seconds
    res['time'] = res['time'].dt.total_seconds()

    return res[['time','running']]

def main():
    p = argparse.ArgumentParser(
        description="Plot vehicles-in-network from summary XMLs"
    )
    p.add_argument('-i','--input', nargs='+', required=True,
                   help='summary XML files')
    p.add_argument('-l','--labels', nargs='+',
                   help='labels matching each input')
    p.add_argument('-b','--binsize', type=float, default=0.0,
                   help='bin width in seconds (0=no binning)')
    p.add_argument('-o','--output', default='running.png',
                   help='output image filename')
    args = p.parse_args()

    if args.labels and len(args.labels) != len(args.input):
        p.error("Number of labels must match number of input files")

    dfs = []
    for xml in args.input:
        if not os.path.isfile(xml):
            p.error(f"File not found: {xml}")
        df = parse_running(xml)
        if args.binsize > 0:
            df = bin_and_agg(df, args.binsize)
        dfs.append(df)

    labels = args.labels or [os.path.basename(f) for f in args.input]
    plt.figure(figsize=(10,5))
    for df, lbl in zip(dfs, labels):
        plt.plot(df['time'], df['running'], marker='o', label=lbl)

    plt.xlabel("Time [s]")
    plt.ylabel("Vehicles in Network")
    plt.title("Active Vehicles Over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    print(f"Saved plot to {args.output}")

if __name__ == '__main__':
    main()
