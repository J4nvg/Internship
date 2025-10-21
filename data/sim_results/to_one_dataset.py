import os
import pandas as pd
import csv
import re

input_folder = "./"
output_file = "combined_dataset.csv"

metrics = [
    "find_steps",
    "taken_down",
    "area_covered",
    "mean_distance_travelled",
    "total_distance_covered",
    "hider_frac_found"
]

# Output columns
columns = [
    "filename", "tactic", "grid_width", "hide_strategy",
    "swarm_size", "n_hider_candidates", "n_hiders", "runs"
]
for metric in metrics:
    columns.extend([
        f"{metric}_min",
        f"{metric}_max",
        f"{metric}_mean",
        f"{metric}_var",
        f"{metric}_ci_lower",
        f"{metric}_ci_upper",
        f"{metric}_half_width"
    ])
columns.append("found")

# Regex pattern to extract info from filenames
pattern = re.compile(
    r"T-(?P<tactic>.+?)-W-(?P<width>\d+)-HS-(?P<hiding_strategy>.+?)-D-(?P<swarm_size>\d+)-C-(?P<candidates>\d+)-H-(?P<hiders>\d+)-RUNS-(?P<runs>\d+)\.csv"
)

all_data = []

for filename in os.listdir(input_folder):
    if not filename.endswith(".csv") or not filename.startswith("T-"):
        continue

    match = pattern.match(filename)
    if not match:
        print(f"⚠️ Skipping unrecognized filename format: {filename}")
        continue

    filepath = os.path.join(input_folder, filename)

    # Read tab-separated file
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        lines = [row for row in reader if row]

    # Build row data
    row_data = {
        "filename": filename,
        "tactic": match.group("tactic"),
        "grid_width": int(match.group("width")),
        "hide_strategy": match.group("hiding_strategy"),
        "swarm_size": int(match.group("swarm_size")),
        "n_hider_candidates": int(match.group("candidates")),
        "n_hiders": int(match.group("hiders")),
        "runs": int(match.group("runs")),
    }

    # Extract metrics
    for row in lines:
        if not row:
            continue
        key = row[0].strip().lower()

        if key in metrics:
            try:
                values = [float(x) for x in row[1:8]]
                row_data.update({
                    f"{key}_min": values[0],
                    f"{key}_max": values[1],
                    f"{key}_mean": values[2],
                    f"{key}_var": values[3],
                    f"{key}_ci_lower": values[4],
                    f"{key}_ci_upper": values[5],
                    f"{key}_half_width": values[6],
                })
            except (ValueError, IndexError):
                print(f"⚠️ Could not parse values for {key} in {filename}")
                continue

        elif key == "found":
            try:
                val = row[1].strip().replace("%", "")
                row_data["found"] = float(val)
            except (ValueError, IndexError):
                row_data["found"] = None

    all_data.append(row_data)

# Combine and export
df = pd.DataFrame(all_data, columns=columns)
df.to_csv(output_file, index=False)

print(f"Combined dataset saved as {output_file}")
print(f"Total files processed: {len(all_data)}")
