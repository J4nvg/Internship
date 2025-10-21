"""
Plotting script for updated simulation results.
Handles new file structure, additional metrics, and 45-run statistical comparisons.
Generates distribution plots, aggregated barplots, and heatmaps for deep insights.

Author: ASPA-GPT
"""

import os
import re
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ================================================================
# 1. CONFIGURATION
# ================================================================
DATA_DIR = "./data/sim_results"

# Metrics expected in CSV
METRICS = [
    "find_steps",
    "taken_down",
    "area_covered",
    "mean_distance_travelled",
    "total_distance_covered",
    "hider_frac_found"
]

# ================================================================
# 2. FILE LOADING AND PARSING
# ================================================================

def parse_filename(filename):
    """
    Parse filename structure:
    T-{tactic}-W-{width}-HS-{hiding_strategy}-D-{swarm_size}-C-{n_hider_candidates}-H-{n_hiders}-RUNS-{runs}.csv
    """
    pattern = (
        r"T-(?P<tactic>[^-]+)-W-(?P<width>\d+)-HS-(?P<hiding_strategy>[^-]+)"
        r"-D-(?P<swarm_size>\d+)-C-(?P<n_hider_candidates>\d+)"
        r"-H-(?P<n_hiders>\d+)-RUNS-(?P<runs>\d+)"
    )
    match = re.match(pattern, filename.replace(".csv", ""))
    if not match:
        return None
    return match.groupdict()


def load_sim_data(data_dir=DATA_DIR):
    """
    Load all CSVs from the new data folder and return a clean aggregated DataFrame.
    """
    records = []
    for fname in os.listdir(data_dir):
        if not fname.endswith(".csv"):
            continue

        params = parse_filename(fname)
        if not params:
            continue

        path = os.path.join(data_dir, fname)
        df = pd.read_csv(path, sep=r"\s+", index_col=0)

        record = {
            **params,
            "Found_percentage": float(df.loc["Found", "min"].strip("%"))
        }

        for metric in METRICS:
            for col in ["min", "max", "mean", "var", "ci_lower", "ci_upper", "Half_width"]:
                key = f"{metric}_{col}"
                record[key] = df.loc[metric, col]

        records.append(record)

    df_all = pd.DataFrame(records)
    df_all = df_all.astype({
        "width": int,
        "swarm_size": int,
        "n_hider_candidates": int,
        "n_hiders": int,
        "runs": int,
    })
    print(f"Loaded {len(df_all)} simulation result files.")
    return df_all


# ================================================================
# 3. PLOTTING FUNCTIONS
# ================================================================

def plot_metric_distribution(df, metric):
    """
    Show distribution (violin + swarm) of a metric across tactics and swarm sizes.
    """
    plt.figure(figsize=(12, 6))
    sns.violinplot(data=df, x="tactic", y=f"{metric}_mean", hue="swarm_size", split=True)
    plt.title(f"{metric.replace('_', ' ').title()} Distribution by Tactic and Swarm Size")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()


def plot_metric_bar(df, metric):
    """
    Show aggregated bar plot with confidence intervals across hiding strategies.
    """
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=df,
        x="tactic",
        y=f"{metric}_mean",
        hue="swarm_size",
        errorbar=("ci", 95),
        dodge=True
    )
    plt.title(f"{metric.replace('_', ' ').title()} by Tactic and Swarm Size")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()


def plot_metric_by_hiding_strategy(df, metric):
    """
    Faceted barplot per hiding strategy.
    """
    g = sns.catplot(
        data=df,
        x="tactic",
        y=f"{metric}_mean",
        hue="swarm_size",
        col="hiding_strategy",
        kind="bar",
        errorbar=("ci", 95),
        height=4,
        aspect=1
    )
    g.set_titles("{col_name}")
    g.set_axis_labels("Tactic", metric.replace("_", " ").title())
    plt.tight_layout()
    plt.show()


def plot_heatmap(df, metric):
    """
    Heatmap of a metric mean vs tactic and number of hiders.
    """
    pivot = df.pivot_table(values=f"{metric}_mean", index="tactic", columns="n_hiders")
    plt.figure(figsize=(8, 5))
    sns.heatmap(pivot, annot=True, cmap="viridis", fmt=".2f")
    plt.title(f"{metric.replace('_', ' ').title()} vs Tactic and #Hiders")
    plt.tight_layout()
    plt.show()


def plot_pairwise_correlations(df):
    """
    Correlation scatter plots among metrics to visualize trade-offs.
    """
    metric_means = [f"{m}_mean" for m in METRICS]
    sns.pairplot(df, vars=metric_means, hue="tactic", diag_kind="kde", corner=True)
    plt.suptitle("Metric Correlations by Tactic", y=1.02)
    plt.show()


# ================================================================
# 4. MAIN EXECUTION
# ================================================================
if __name__ == "__main__":
    all_data = load_sim_data(DATA_DIR)

    # Example aggregated plots for each metric
    for metric in METRICS:
        plot_metric_bar(all_data, metric)
        plot_metric_by_hiding_strategy(all_data, metric)
        plot_heatmap(all_data, metric)

    # Optional deeper plots
    plot_pairwise_correlations(all_data)
    plot_metric_distribution(all_data, "hider_frac_found")

    print("✅ Plot generation complete.")
