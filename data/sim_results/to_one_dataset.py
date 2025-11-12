import os
import pandas as pd
import csv
import re
import sys

metrics = [
    "steps",
    "taken_down",
    "area_covered",
    "mean_distance_travelled",
    "total_distance_covered",
    "hider_frac_found",
    "all_found"
]

# Output columns
columns = [
    "filename", "tactic", "grid_width", "hide_strategy",
    "swarm_size", "n_hider_candidates", "n_hiders", "runs"
]

for metric in metrics:
    if metric == "all_found":
        columns.extend([
            f"{metric}_mean",
            f"{metric}_ci_lower",
            f"{metric}_ci_upper"
        ])
    else:
        columns.extend([
            f"{metric}_min",
            f"{metric}_max",
            f"{metric}_mean",
            f"{metric}_var",
            f"{metric}_ci_lower",
            f"{metric}_ci_upper",
            f"{metric}_half_width"
        ])

# Regex pattern to extract info from filenames
pattern = re.compile(
    r"T-(?P<tactic>.+?)-W-(?P<width>\d+)-HS-(?P<hiding_strategy>.+?)-D-(?P<swarm_size>\d+)-C-(?P<candidates>\d+)-H-(?P<hiders>\d+)-RUNS-(?P<runs>\d+)\.csv"
)


# os.path.join(f"data", f"sim_results", f"{p_dist}")
# input_folder = f"./data/sim_results"
input_folder_main = f"./"
output_path = f"../dataset/"

# Create a list of subdirectories
subdirs = list(os.walk(input_folder_main))[0][1]

for subdir in subdirs:
    all_data = []
    input_folder = os.path.join(input_folder_main, subdir)

    output_folder = os.path.join(output_path, subdir)
    os.makedirs(output_folder, exist_ok=True)

    output_file = os.path.join(output_path, subdir, "sim_results_dataset.csv")

    for filename in os.listdir(input_folder):
        if not filename.endswith(".csv") or not filename.startswith("T-"):
            continue

        match = pattern.match(filename)
        if not match:
            print(f"Skipping unrecognized filename format: {filename}")
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
                if key == "all_found":
                    values = [x for x in row[1:8]]
                    row_data.update({
                        f"{key}_mean": values[2],
                        f"{key}_ci_lower": values[4],
                        f"{key}_ci_upper": values[5],
                    })
                else:
                    values = [x for x in row[1:8]]
                    row_data.update({
                        f"{key}_min": values[0],
                        f"{key}_max": values[1],
                        f"{key}_mean": values[2],
                        f"{key}_var": values[3],
                        f"{key}_ci_lower": values[4],
                        f"{key}_ci_upper": values[5],
                        f"{key}_half_width": values[6],
                    })
        all_data.append(row_data)

    # Combine and export
    df = pd.DataFrame(all_data, columns=columns)
    df.to_csv(output_file, index=False)

    print(f"Combined dataset saved as {output_file}")
    print(f"Total files processed: {len(all_data)}")
