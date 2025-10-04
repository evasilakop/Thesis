#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import argparse

def parse_emissions(xml_file):
    """
    Parse edge-emissions XML into DataFrame with columns:
      time, CO2, NOx, PMx  (all summed per timestep)
    """
    rows = []
    tree = ET.parse(xml_file)
    for step in tree.getroot().findall('timestep'):
        t = float(step.get('time', step.get('begin', 0.0)))
        co2 = sum(float(v.get('CO2', 0.0)) for v in step.findall('vehicle'))
        nox = sum(float(v.get('NOx', 0.0)) for v in step.findall('vehicle'))
        pmx = sum(float(v.get('PMx', 0.0)) for v in step.findall('vehicle'))
        rows.append({'time': t, 'CO2': co2, 'NOx': nox, 'PMx': pmx})
    return pd.DataFrame(rows)

def bin_mean(df, bin_size):
    """
    Resample df into fixed-width bins (bin_size seconds),
    computing the mean of each column in that bin.
    Returns a DataFrame with columns ['time', ...metrics...].
    """
    # set a TimedeltaIndex
    df.index   = pd.to_timedelta(df['time'], unit='s')
    df.index.name = 'time'
    # drop original time column to avoid duplication
    df = df.drop(columns='time')
    # compute mean per bin
    agg = df.resample(f'{int(bin_size)}s').mean().reset_index()
    # convert index back to float seconds
    agg['time'] = agg['time'].dt.total_seconds()
    return agg


def main():
    p = argparse.ArgumentParser(
        description="Generate LaTeX table of mean emissions per interval"
    )
    p.add_argument('-i','--inputs', nargs=2, required=True,
                   help='Two edge-emissions XML files: proposed.xml standard.xml')
    p.add_argument('-l','--labels', nargs=2, default=['Proposed','Standard'],
                   help='Labels for the two cases')
    p.add_argument('-b','--binsize', type=float, default=60.0,
                   help='Bin width in seconds (default: 60)')
    p.add_argument('-o','--output', required=True,
                   help='Output .tex file for the LaTeX table')
    args = p.parse_args()

    xml_p, xml_s = args.inputs
    lbl_p, lbl_s = args.labels

    # Parse and bin each run
    df_p = bin_mean(parse_emissions(xml_p), args.binsize)
    df_s = bin_mean(parse_emissions(xml_s), args.binsize)

    # Build MultiIndex columns
    metrics = ['CO₂ [mg]','NOₓ [mg]','PMx [mg]']
    cases   = [lbl_p, lbl_s]
    cols = pd.MultiIndex.from_product([metrics, cases],
                                      names=['Metric','Case'])

    # Assemble data array: time + alternating columns
    data = np.column_stack([
        df_p['time'],
        df_p['CO2'], df_s['CO2'],
        df_p['NOx'], df_s['NOx'],
        df_p['PMx'], df_s['PMx']
    ])

    # Build DataFrame
    df_table = pd.DataFrame(data,
                            columns=['Time [s]'] + list(cols))
    # Round numeric columns
    for m in ['CO₂ [mg]','NOₓ [mg]','PMx [mg]']:
        df_table[(m,lbl_p)] = df_table[(m,lbl_p)].astype(float).round(1)
        df_table[(m,lbl_s)] = df_table[(m,lbl_s)].astype(float).round(1)

    # Export LaTeX
    tex = df_table.to_latex(
        index=False,
        header=True,
        multirow=True,
        column_format='r|' + 'rr|'*3,
        escape=False,
        float_format="%.2f"
    )

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(tex)
    print(f"Wrote emissions table to {args.output}")

if __name__=='__main__':
    main()
