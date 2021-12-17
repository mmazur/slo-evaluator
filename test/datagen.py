#!/usr/bin/env python3

import click
import pandas as pd
import numpy as np


def_count = 100
def_metricname = "node_temp_celsius"
def_minval = 45
def_maxval = 100
def_idcolheader = "id"
def_step = 10 # seconds

startts = 1610000000
rng = np.random.default_rng()


def gen_metric(count=def_count, step=def_step, metricname=def_metricname,
               minval=def_minval, maxval=def_maxval, columns=[]):
    timestamps = pd.DataFrame(range(startts, startts+(count*step), step), columns=["timestamp"])
    values = pd.DataFrame(rng.integers(minval, maxval, size=(count, 1)), columns=["value"])

    df = pd.concat([timestamps, values], axis=1)
    df.set_index("timestamp", inplace=True)

    df.insert(0, "__name__", metricname)

    for header, value in columns:
        df.insert(df.shape[1]-1, header, value)

    return df


def gen_metrics(count=def_count, step=def_step, metricname=def_metricname, minval=def_minval,
                maxval=def_maxval, columns=[], idcolumns=[]):
    if idcolumns:
        dfs = []
        for header, value in idcolumns:
            periddf = gen_metric(count, step, metricname, minval, maxval, [(header, value)])
            dfs.append(periddf)
        df = pd.concat(dfs)
    else:
        df = gen_metric(count, step, metricname, minval, maxval)

    df.sort_index(inplace=True)

    for header, value in columns:
        df.insert(df.shape[1], header, value)

    return df


@click.command()
@click.option("--count", "-c", default=def_count, help=f"Number of rows per single system (default: {def_count})")
@click.option("--step", "-s", default=def_step,
                                    help=f"Time delta between data points, in seconds (default: {def_step}")
@click.option("--metric-name", "-m", "metricname", default=def_metricname,
                                    help=f"Metric name (default: '{def_metricname}')")
@click.option("--min", "minval", default=def_minval, help=f"Minimum generated value (default: {def_minval})")
@click.option("--max", "maxval", default=def_maxval, help=f"Minimum generated value (default: {def_maxval})")
@click.option("--column", "_columns", default=None, multiple=True,
                                    help="Add an arbitrary column (format: header=value). Can be used multiple times.")
@click.option("--id-column-header", "idcolheader", default=def_idcolheader,
                                    help=f"Column name (header) for system ids (default: '{def_idcolheader}')")
@click.option("--ids", default=None, type=str, help="System ids, comma separated (default: none)")
@click.option("--output", "-o", default=None, type=str, help="Output file (default: stdout)")
def main(count, step, metricname, minval, maxval, _columns, idcolheader, ids, output):
    # Parse everything fully first
    columns = []
    for col in _columns:
        header, value = col.split("=")
        columns.append((header, value))

    idcolumns = []
    if ids:
        for value in set(ids.split(',')):
            idcolumns.append((idcolheader, value))

    # Generate data
    df = gen_metrics(count=count, step=step, metricname=metricname,
                     minval=minval, maxval=maxval,
                     columns=columns, idcolumns=idcolumns)

    # Output data
    if output is None or output=='-':
        print(df.to_csv(),end='')
    else:
        df.to_csv(output)


if __name__ == "__main__":
    main()

