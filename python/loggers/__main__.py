"""
Convert a TimeSeriesLogger JSON file to CSV.

Usage (from the python/ directory):
  python3 -m loggers <file.json> [out.csv]
"""

import sys

from .convert import json_to_csv

if len(sys.argv) not in (2, 3):
    sys.exit(__doc__)
print(json_to_csv(*sys.argv[1:]))
