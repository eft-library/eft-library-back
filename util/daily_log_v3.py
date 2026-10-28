"""Collect combined server output into daily files using Korea time."""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def collect_daily_logs_v3(stream_v3, directory_v3):
    directory_v3 = Path(directory_v3)
    directory_v3.mkdir(parents=True, exist_ok=True)
    timezone_v3 = ZoneInfo("Asia/Seoul")
    current_date_v3 = None
    output_v3 = None
    try:
        for line_v3 in stream_v3:
            date_v3 = datetime.now(timezone_v3).strftime("%Y-%m-%d")
            if date_v3 != current_date_v3:
                if output_v3 is not None:
                    output_v3.close()
                output_v3 = (directory_v3 / f"{date_v3}.out").open("ab", buffering=0)
                current_date_v3 = date_v3
            output_v3.write(line_v3)
    finally:
        if output_v3 is not None:
            output_v3.close()


if __name__ == "__main__":
    collect_daily_logs_v3(sys.stdin.buffer, sys.argv[1])
