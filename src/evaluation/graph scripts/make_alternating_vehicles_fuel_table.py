#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import argparse

def parse_summary(xml_file):
    """
    Parse <step> summary XML into DataFrame with:
      time, running, halting
    """
    tree = ET.parse(xml_file)
    rows = []
    for step in tree.getroot().findall('step'):
        t       = float(step.get('time', step.get('begin', 0.0)))
        running = float(step.get('running', 0.0))
        halting = float(step.get('halting', 0.0))
        rows.append({'time': t, 'running': running, 'halting': halting})
    return pd.DataFrame(rows)

def parse_emissions(xml_file):
    """
    Parse edge-emissions XML into DataFrame with:
      time, fuel
    """
    tree = ET.parse(xml_file)
    rows = []
    for step in tree.getroot().findall('timestep'):
        t    = float(step.get('time', step.get('begin', 0.0)))
        fuel = sum(float(v.get('fuel', 0.0)) for v in step.findall('vehicle'))
        rows.append({'time': t, 'fuel': fuel})
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
        description="Make LaTeX table: vehicles & halting + fuel, Proposed vs Standard"
    )
    p.add_argument(
        '-i','--summary', nargs=2, required=True,
        help='Two summary XMLs: proposed_summary.xml standard_summary.xml'
    )
    p.add_argument(
        '-e','--emissions', nargs=2, required=True,
        help='Two edge-emissions XMLs: proposed_emissions.xml standard_emissions.xml'
    )
    p.add_argument(
        '-l','--labels', nargs=2, default=['Proposed','Standard'],
        help='Labels for the two runs'
    )
    p.add_argument(
        '-b','--binsize', type=float, default=60.0,
        help='Bin width in seconds (default: 60)'
    )
    p.add_argument(
        '-o','--output', required=True,
        help='Output .tex filename'
    )
    args = p.parse_args()

    summary_p, summary_s = args.summary
    em_p, em_s           = args.emissions
    lbl_p, lbl_s         = args.labels

    # parse & bin summaries
    df_sum_p = bin_mean(parse_summary(summary_p), args.binsize)
    df_sum_s = bin_mean(parse_summary(summary_s), args.binsize)

    # parse & bin emissions
    df_em_p  = bin_mean(parse_emissions(em_p), args.binsize)
    df_em_s  = bin_mean(parse_emissions(em_s), args.binsize)

    # merge all on 'time'
    df = pd.merge(df_sum_p, df_sum_s, on='time', suffixes=(f'_{lbl_p}', f'_{lbl_s}'))
    df = pd.merge(df,     df_em_p,  on='time')
    df = pd.merge(df,     df_em_s,  on='time', suffixes=(f'_emP', f'_{lbl_s}'))
    # rename emission columns
    df = df.rename(columns={
        'fuel_emP': f'fuel_{lbl_p}',
        f'fuel_{lbl_s}': f'fuel_{lbl_s}'
    })

    # build MultiIndex for columns
    metrics = [
        ('Vehicles in Network', lbl_p),
        ('Vehicles in Network', lbl_s),
        ('Halting Vehicles',      lbl_p),
        ('Halting Vehicles',      lbl_s),
        ('Fuel [mg]',             lbl_p),
        ('Fuel [mg]',             lbl_s)
    ]
    mi = pd.MultiIndex.from_tuples(metrics, names=['Metric','Case'])

    # assemble table data
    data = np.column_stack([
        df['time'],
        df[f'running_{lbl_p}'], df[f'running_{lbl_s}'],
        df[f'halting_{lbl_p}'], df[f'halting_{lbl_s}'],
        df[f'fuel_{lbl_p}'], df[f'fuel_{lbl_s}']
    ])

    table = pd.DataFrame(data, columns=['Time [s]'] + list(mi))
    # round numerical columns
    for col in table.columns[1:7]:
        table[col] = table[col].astype(float).round(1)

    # export to LaTeX
    tex = table.to_latex(
        index=False,
        header=True,
        multirow=True,
        column_format='r|' + 'rr|' * 3 + 'rr',
        escape=False,
        float_format="%.2f"
    )

    with open(args.output, 'w') as f:
        f.write(tex)
    print(f"Wrote LaTeX table to {args.output}")

if __name__ == '__main__':
    main()
