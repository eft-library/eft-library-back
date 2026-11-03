"""Collect combined server output into daily files using Korea time."""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def collect_daily_logs(stream, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    timezone = ZoneInfo("Asia/Seoul")
    current_date = None
    output = None
    try:
        for line in stream:
            date = datetime.now(timezone).strftime("%Y-%m-%d")
            if date != current_date:
                if output is not None:
                    output.close()
                output = (directory / f"{date}.out").open("ab", buffering=0)
                current_date = date
            output.write(line)
    finally:
        if output is not None:
            output.close()


if __name__ == "__main__":
    collect_daily_logs(sys.stdin.buffer, sys.argv[1])
