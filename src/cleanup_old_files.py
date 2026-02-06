"""
Delete files from data/raw folder that contain 2022, 2023 or 2024 in their filename.
"""

from pathlib import Path

TARGET_DIR = Path("data/raw")
YEARS_TO_DELETE = ["2021","2022", "2023", "2024"]

deleted = 0
for file in TARGET_DIR.iterdir():
    if file.is_file():
        if any(year in file.name for year in YEARS_TO_DELETE):
            print(f"Deleting: {file.name}")
            file.unlink()
            deleted += 1

print(f"\nDone! Deleted {deleted} file(s).")