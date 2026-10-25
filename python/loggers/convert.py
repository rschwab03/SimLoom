"""Convert a TimeSeriesLogger JSON file to CSV (CLI: python3 -m loggers)."""

import csv
import json
import os


def json_to_csv(json_path: str, csv_path: str = None) -> str:
    """Write the "t" and "signals" columns of a time-series JSON as CSV.

    Columns are `t` followed by one column per signal; null values become
    empty cells. Returns the CSV path (defaults to json_path with .csv).
    """
    if csv_path is None:
        csv_path = os.path.splitext(json_path)[0] + ".csv"
    with open(json_path) as f:
        record = json.load(f)

    t = record["t"]
    signals = record["signals"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t", *signals])
        for i, time in enumerate(t):
            row = [time] + ["" if col[i] is None else col[i] for col in signals.values()]
            writer.writerow(row)
    return csv_path

