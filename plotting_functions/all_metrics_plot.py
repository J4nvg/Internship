import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
from pathlib import Path
import sys

# --- Configuration ---
sns.set_palette("husl")
# Use the data path from your original script
DATA_PATH = "../data/sim_results"


# --- Data Loading (from Inspiration Code) ---

def parse_filename(filename):
    """
    Parse filename format:
    T-{tactic}-W-{width}-HS-{hide_strategy}-D-{swarm_size}-C-{n_hider_candidates}-H-{n_hiders}-RUNS-{runs}.csv
    """
    # Remove .csv and split by '-'
    parts = os.path.basename(filename).replace('.csv', '').split('-')
    try:
        return {
            'tactic': parts[1],
            'width': int(parts[3]),
            'hide_strategy': parts[5],  # FIX: Changed from hiding_strategy
            'swarm_size': int(parts[7]),
            'n_hider_candidates': int(parts[9]),
            'n_hiders': int(parts[11]),
            'runs': int(parts[13])
        }
    except (IndexError, ValueError) as e:
        print(f"Warning: Could not parse filename '{filename}'. Error: {e}")
        return None


def load_all_results(data_path=DATA_PATH, force_rebuild=False):
    """
    Load all individual CSV files, combine them, and save as combined_dataset.csv.
    If combined_dataset.csv exists, load it directly unless force_rebuild=True.
    """
    combined_csv_path = os.path.join(data_path, "combined_dataset.csv")

    # 1. Try loading the existing combined file first
    if not force_rebuild and os.path.exists(combined_csv_path):
        print(f"Loading existing combined dataset from: {combined_csv_path}")
        try:
            return pd.read_csv(combined_csv_path)
        except Exception as e:
            print(f"Warning: Could not load combined dataset: {e}. Rebuilding...")

    # 2. If it fails or force_rebuild=True, build from raw files
    print("Building combined dataset from raw CSV files...")
    records = []

    # Find all CSVs in the directory
    csv_files = glob.glob(os.path.join(data_path, "*.csv"))

    if not csv_files:
        print(f"Error: No raw CSV files found in {data_path}")
        return pd.DataFrame()  # Return empty DF

    for filepath in csv_files:
        filename = os.path.basename(filepath)

        # Skip the combined file itself
        if filename == "combined_dataset.csv":
            continue

        params = parse_filename(filename)
        if params is None:
            continue  # Skip files that can't be parsed

        try:
            # Use the separator from inspiration code, as it's for raw files
            df = pd.read_csv(filepath, sep=r"\s+", index_col=0)
        except Exception as e:
            print(f"Warning: Skipping file. Could not read '{filename}'. Error: {e}")
            continue

        record = {
            "tactic": params['tactic'],
            "hide_strategy": params['hide_strategy'],  # FIX: Changed from hiding_strategy
            "swarm_size": params['swarm_size'],
            "n_hiders": params['n_hiders'],
            "n_hider_candidates": params['n_hider_candidates'],
            "width": params['width'],
            "runs": params['runs'],
        }

        # --- Map Metric Names ---
        # Map names from raw files (e.g., 'steps') to names
        # expected by your original plotter (e.g., 'steps_mean')
        metrics_map = {
            'steps': 'steps',
            'taken_down': 'taken_down',
            'area_covered': 'area_covered',
            'mean_distance_travelled': 'mean_distance_travelled',
            'total_distance_covered': 'total_distance_covered',
            'hider_frac_found': 'hider_frac_found'
        }

        for metric_in_file, metric_out_col in metrics_map.items():
            if metric_in_file in df.index:
                # Add columns for BOTH original and new plotters
                mean = df.loc[metric_in_file, "mean"]
                hw = df.loc[metric_in_file, "Half_width"]
                ci_low = df.loc[metric_in_file, "ci_lower"]
                ci_up = df.loc[metric_in_file, "ci_upper"]

                # For your original plotter
                record[f"{metric_out_col}_mean"] = mean
                record[f"{metric_out_col}_half_width"] = hw

                # For new plotters from inspiration
                # FIX: Changed to _ci_lower and _ci_upper to match CSV and avoid KeyError
                record[f"{metric_out_col}_ci_lower"] = ci_low
                record[f"{metric_out_col}_ci_upper"] = ci_up
                # FIX: Removed redundant '_hw' column. We will use '_half_width' everywhere.

        if 'Found' in df.index:
            found_val = df.loc["Found", "min"]
            record["found_percentage"] = float(str(found_val).strip("%"))

        records.append(record)

    if not records:
        print("Error: No valid data records were built.")
        return pd.DataFrame()

    combined_df = pd.DataFrame(records)

    # 3. Save the new combined file
    try:
        combined_df.to_csv(combined_csv_path, index=False)
        print(f"Saved new combined dataset to: {combined_csv_path}")
    except Exception as e:
        print(f"Error saving combined dataset: {e}")

    return combined_df


# --- Plot 1: Original FacetGrid Grouped Bars ---

def plot_grouped_bars(data, x, y, yerr_col, hue_col, palette, **kwargs):
    """
    Helper function to be mapped onto a FacetGrid.
    This function plots grouped bars with custom error bars (from yerr_col).
    (This is your original, unmodified function)
    """
    # Fix: Remove 'color' from kwargs passed by map_dataframe
    kwargs.pop('color', None)
    ax = plt.gca()
    hue_levels = sorted(data[hue_col].unique())
    n_hues = len(hue_levels)
    x_levels = sorted(data[x].unique())
    x_pos = np.arange(len(x_levels))
    total_width = 0.8
    width = total_width / n_hues
    offsets = np.linspace(-total_width / 2 + width / 2, total_width / 2 - width / 2, n_hues)
    colors = sns.color_palette(palette, n_colors=n_hues)

    for i, hue in enumerate(hue_levels):
        hue_data = data[data[hue_col] == hue].set_index(x).reindex(x_levels)
        y_values = hue_data[y]
        y_errors = hue_data[yerr_col]
        ax.bar(
            x_pos + offsets[i],
            y_values,
            width=width,
            yerr=y_errors,
            capsize=4,
            color=colors[i],
            label=hue,
            **kwargs
        )
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_levels)
    ax.set_xlabel(x)
    ax.set_ylabel(y.replace('_', ' ').title())


def generate_grouped_bar_plots(df):
    """
    Generates the original set of faceted, grouped bar plots.
    (This is your original main function, modified to accept a DataFrame)
    """
    if df.empty:
        print("Skipping grouped bar plots: DataFrame is empty.")
        return

    # --- 1. Define Metrics ---
    metrics_to_plot = {
        'steps_mean': 'steps_half_width',
        'taken_down_mean': 'taken_down_half_width',
        'area_covered_mean': 'area_covered_half_width',
        'mean_distance_travelled_mean': 'mean_distance_travelled_half_width',
        'hider_frac_found_mean': 'hider_frac_found_half_width'
    }

    # Check if required columns exist before proceeding
    required_cols = list(metrics_to_plot.keys()) + list(metrics_to_plot.values())

    # Check for 'hide_strategy' as well
    if 'hide_strategy' not in df.columns:
        print("Skipping grouped bar plots: 'hide_strategy' column not found.")
        return

    if not all(col in df.columns for col in required_cols):
        print("Skipping grouped bar plots: Not all required metric columns found.")
        print(f"Missing: {[col for col in required_cols if col not in df.columns]}")
        return

    # --- 2. Loop and Plot Each Metric ---
    for y_metric, y_error in metrics_to_plot.items():
        print(f"Generating plot for: {y_metric}...")
        sns.set(style="whitegrid", context="talk")
        g = sns.FacetGrid(
            df,
            row='tactic',
            col='hide_strategy',  # FIX: Changed from hiding_strategy
            sharex=True,
            sharey=False,
            height=4.5,
            aspect=1.2,
            margin_titles=True
        )
        g.map_dataframe(
            plot_grouped_bars,
            x='swarm_size',
            y=y_metric,
            yerr_col=y_error,
            hue_col='n_hiders',
            palette='deep'
        )
        g.add_legend(title='n_hiders')
        g.set_titles(row_template='Tactic: {row_name}', col_template='Hide Strategy: {col_name}')

        plot_title = y_metric.replace('_mean', '').replace('hider_frac_', '').replace('_', ' ').title()
        if 'Found' in plot_title:
            plot_title = "Hider Found (Mean Fraction)"
        g.fig.suptitle(f"Metric Analysis: {plot_title}", y=1.03, fontsize=20, fontweight='bold')

        g.fig.tight_layout()
        output_filename = f"{y_metric}_visualization.png"
        plt.savefig(output_filename, bbox_inches='tight', dpi=150)
        print(f"Saved plot to {output_filename}")
        plt.close(g.fig)


# --- Plot 2: Line plots showing trends (from Inspiration) ---
def plot_trends_by_n_hiders(data, metric='steps'):
    """Line plot: metric vs n_hiders, faceted by hiding strategy, colored by swarm size"""
    hiding_strategies = sorted(data['hide_strategy'].unique())  # FIX: Changed from hiding_strategy
    if not hiding_strategies:
        print(f"Skipping trend plot for {metric}: No hiding strategies found.")
        return

    fig, axes = plt.subplots(1, len(hiding_strategies), figsize=(18, 5), sharey=True)
    if len(hiding_strategies) == 1:
        axes = [axes]

    for ax, hiding_strat in zip(axes, hiding_strategies):
        subset = data[data['hide_strategy'] == hiding_strat]  # FIX: Changed from hiding_strategy

        for tactic in sorted(subset['tactic'].unique()):
            tactic_data = subset[subset['tactic'] == tactic]

            for swarm in sorted(tactic_data['swarm_size'].unique()):
                swarm_data = tactic_data[tactic_data['swarm_size'] == swarm].sort_values('n_hiders')

                # Use the metric names created by load_all_results
                ax.plot(swarm_data['n_hiders'], swarm_data[f'{metric}_mean'],
                        marker='o', label=f"{tactic} (S={swarm})", alpha=0.7)

                # FIX: Changed to _ci_lower and _ci_upper to match CSV
                ax.fill_between(swarm_data['n_hiders'],
                                swarm_data[f'{metric}_ci_lower'],
                                swarm_data[f'{metric}_ci_upper'], alpha=0.2)

        ax.set_title(f"Hiding: {hiding_strat}")
        ax.set_xlabel("Number of Hiders")
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel(metric.replace('_', ' ').title())
    axes[-1].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

    plt.suptitle(f"{metric.replace('_', ' ').title()} vs Number of Hiders", fontsize=14, y=1.02)
    plt.tight_layout()

    output_filename = f"trends_{metric}.png"
    plt.savefig(output_filename, bbox_inches='tight', dpi=150)
    print(f"Saved plot to {output_filename}")
    plt.close(fig)


# --- Plot 3: Heatmap for each tactic (from Inspiration) ---
def plot_heatmap_by_tactic(data, metric='steps'):
    """Heatmap: swarm_size vs n_hiders, faceted by tactic and hiding strategy"""
    tactics = sorted(data['tactic'].unique())
    hiding_strategies = sorted(data['hide_strategy'].unique())  # FIX: Changed from hiding_strategy

    if not tactics or not hiding_strategies:
        print(f"Skipping heatmap for {metric}: No tactics or hiding strategies found.")
        return

    fig, axes = plt.subplots(len(hiding_strategies), len(tactics),
                             figsize=(4 * len(tactics) + 2, 4 * len(hiding_strategies)))

    # Ensure axes is always a 2D array
    if len(hiding_strategies) == 1 and len(tactics) == 1:
        axes = np.array([[axes]])
    elif len(hiding_strategies) == 1:
        axes = axes.reshape(1, -1)
    elif len(tactics) == 1:
        axes = axes.reshape(-1, 1)

    for i, hiding_strat in enumerate(hiding_strategies):
        for j, tactic in enumerate(tactics):
            ax = axes[i, j]
            subset = data[(data['tactic'] == tactic) &
                          (data['hide_strategy'] == hiding_strat)]  # FIX: Changed from hiding_strategy

            if subset.empty:
                ax.set_title(f"{tactic} | {hiding_strat}\n(No Data)")
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            try:
                pivot = subset.pivot_table(values=f'{metric}_mean',
                                           index='swarm_size',
                                           columns='n_hiders')

                sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd',
                            ax=ax, cbar_kws={'label': metric})
                ax.set_title(f"{tactic} | {hiding_strat}")
                ax.set_xlabel("Number of Hiders")
                ax.set_ylabel("Swarm Size")
            except Exception as e:
                ax.set_title(f"{tactic} | {hiding_strat}\n(Plot Error)")
                print(f"Error pivoting for heatmap: {e}")

    plt.suptitle(f"{metric.replace('_', ' ').title()} Heatmap", fontsize=16, y=1.00)
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    output_filename = f"heatmap_{metric}.png"
    plt.savefig(output_filename, bbox_inches='tight', dpi=150)
    print(f"Saved plot to {output_filename}")
    plt.close(fig)


def plot_grouped_bars_with_errors(data, metric='steps', group_by='n_hiders'):
    """Bar chart comparing tactics, grouped by n_hiders or swarm_size"""

    # Set style for this plot
    sns.set(style="whitegrid", context="talk")

    hiding_strategies = sorted(data['hide_strategy'].unique())  # FIX: Changed from hiding_strategy
    if not hiding_strategies:
        print(f"Skipping grouped bars for {metric}: No hiding strategies found.")
        return

    # FIX: Increased height from 7 to 8 for better vertical label spacing
    fig, axes = plt.subplots(1, len(hiding_strategies), figsize=(20, 8), sharey=True)
    if len(hiding_strategies) == 1:
        axes = [axes]

    # --- FIX: Removed the tactic_label_map ---

    # --- FIX: Variables to store legend handles/labels ---
    handles = None
    labels = None

    for ax, hiding_strat in zip(axes, hiding_strategies):
        subset = data[data['hide_strategy'] == hiding_strat]  # FIX: Changed from hiding_strategy

        x_var = 'tactic'
        hue_var = 'swarm_size' if group_by == 'n_hiders' else 'n_hiders'

        # Get sorted category lists
        x_cats = sorted(subset[x_var].unique())
        hue_cats = sorted(subset[hue_var].unique())
        num_hue = len(hue_cats)

        # Create grouped bar plot using seaborn
        # We pass order and hue_order to ensure alignment with manual error bars
        sns.barplot(data=subset, x=x_var, y=f'{metric}_mean',
                    hue=hue_var, errorbar=None, ax=ax, dodge=True,
                    palette='deep', order=x_cats, hue_order=hue_cats)

        # --- FIX: Grab handles/labels from first plot, then remove legend ---
        if ax == axes[0]:
            handles, labels = ax.get_legend_handles_labels()

        if ax.get_legend():
            ax.get_legend().remove()
        # --- End Legend Fix ---

        # --- Add error bars manually ---
        # Calculate bar positions
        x_pos = np.arange(len(x_cats))
        total_width = 0.8
        width = total_width / num_hue
        offsets = np.linspace(-total_width / 2 + width / 2, total_width / 2 - width / 2, num_hue)

        for i, x_val in enumerate(x_cats):
            for j, hue_val in enumerate(hue_cats):
                # Re-filter subset for error bar data
                sub = subset[(subset[x_var] == x_val) & (subset[hue_var] == hue_val)]
                if sub.empty:
                    continue

                y = sub[f"{metric}_mean"].values[0]
                # FIX: Changed from _hw to _half_width to match CSV and Plot 1
                hw = sub[f"{metric}_half_width"].values[0]
                x = x_pos[i] + offsets[j]

                # This plots the error bar centered on y (the mean)
                ax.errorbar(x, y, yerr=hw, fmt="none", c="black", capsize=3, lw=1)

        ax.set_title(f"Hiding: {hiding_strat}")
        ax.set_xlabel("Tactic")

        # --- FIX: Apply readable x-axis labels ---
        # We don't need ax.set_xticklabels() because sns.barplot does it
        # when we pass the 'order' parameter.
        ax.tick_params(axis='x', rotation=90)  # Changed from 0 to 90
        # --- End X-label Fix ---

        ax.grid(True, alpha=0.3, axis='y')

    axes[0].set_ylabel(metric.replace('_', ' ').title())

    # --- FIX: Add a single, clean legend ---
    if handles:
        axes[-1].legend(handles, labels,
                        title=hue_var.replace('_', ' ').title(),
                        bbox_to_anchor=(1.05, 1), loc='upper left')
    # --- End Legend Fix ---

    plt.suptitle(f"{metric.replace('_', ' ').title()} by Tactic and {hue_var.replace('_', ' ').title()}",
                 fontsize=14, y=1.02)  # Adjusted y for suptitle

    # FIX: Adjust layout to prevent suptitle/legend and give space for vertical labels
    plt.tight_layout(rect=[0, 0.1, 0.9, 0.95])  # Increased bottom margin (0.1)

    output_filename = f"grouped_bars_{metric}_{group_by}.png"
    plt.savefig(output_filename, bbox_inches='tight', dpi=150)
    print(f"Saved plot to {output_filename}")
    plt.close(fig)


# === END OF MODIFIED FUNCTION ===


# --- Plot 5: Multi-metric comparison grid (from Inspiration) ---
def plot_multi_metric_comparison(data, metrics=['steps', 'area_covered',
                                                'hider_frac_found', 'taken_down']):
    """4-panel plot showing multiple metrics for quick comparison"""
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    axes = axes.flatten()

    # Example config: Filter for one swarm size and hiding strategy
    # You can change these values
    FILTER_SWARM_SIZE = 5
    FILTER_HIDE_STRATEGY = 'greedy'

    subset = data[(data['swarm_size'] == FILTER_SWARM_SIZE) &
                  (data['hide_strategy'] == FILTER_HIDE_STRATEGY)]  # FIX: Changed from hiding_strategy

    if subset.empty:
        print(
            f"Skipping multi-metric plot: No data for swarm_size={FILTER_SWARM_SIZE} and strategy='{FILTER_HIDE_STRATEGY}'")
        plt.close(fig)
        return

    for ax, metric in zip(axes, metrics):
        for tactic in sorted(subset['tactic'].unique()):
            tactic_data = subset[subset['tactic'] == tactic].sort_values('n_hiders')

            if tactic_data.empty:
                continue

            ax.plot(tactic_data['n_hiders'], tactic_data[f'{metric}_mean'],
                    marker='o', label=tactic, linewidth=2)

            # FIX: Changed to _ci_lower and _ci_upper to match CSV
            ax.fill_between(tactic_data['n_hiders'],
                            tactic_data[f'{metric}_ci_lower'],
                            tactic_data[f'{metric}_ci_upper'], alpha=0.2)

        ax.set_title(metric.replace('_', ' ').title())
        ax.set_xlabel("Number of Hiders")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    plt.suptitle(f"Multi-Metric Comparison (Swarm={FILTER_SWARM_SIZE}, Hiding={FILTER_HIDE_STRATEGY})", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_filename = "../plots/multi_metric_comparison.png"
    plt.savefig(output_filename, bbox_inches='tight', dpi=150)
    print(f"Saved plot to {output_filename}")
    plt.close(fig)


# --- Plot 6: Performance summary (from Inspiration) ---
def plot_performance_summary(data, metric='hider_frac_found'):
    """Box plot showing distribution of metric across all parameter combinations"""
    hiding_strategies = sorted(data['hide_strategy'].unique())  # FIX: Changed from hiding_strategy
    if not hiding_strategies:
        print(f"Skipping performance summary for {metric}: No hiding strategies found.")
        return

    fig, axes = plt.subplots(1, len(hiding_strategies), figsize=(18, 6), sharey=True)
    if len(hiding_strategies) == 1:
        axes = [axes]

    for ax, hiding_strat in zip(axes, hiding_strategies):
        subset = data[data['hide_strategy'] == hiding_strat]  # FIX: Changed from hiding_strategy

        sns.boxplot(data=subset, x='tactic', y=f'{metric}_mean',
                    hue='swarm_size', ax=ax, palette='pastel')
        ax.set_title(f"Hiding: {hiding_strat}")
        ax.set_xlabel("Tactic")
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(title='Swarm Size', loc='best')

    plt.suptitle(f"{metric.replace('_', ' ').title()} Distribution by Tactic", fontsize=14, y=1.00)
    plt.tight_layout()

    output_filename = f"summary_boxplot_{metric}.png"
    plt.savefig(output_filename, bbox_inches='tight', dpi=150)
    print(f"Saved plot to {output_filename}")
    plt.close(fig)


# --- Main execution ---
if __name__ == "__main__":
    # Load data
    print("--- Loading simulation results ---")
    # Set force_rebuild=True if you have new raw CSV files
    all_data = load_all_results(force_rebuild=False)

    if all_data.empty:
        print("\nNo data loaded. Exiting.")
    else:
        # --- Check for essential columns ---
        # This helps debug if 'combined_dataset.csv' is old or malformed
        required_columns = ['tactic', 'hide_strategy', 'swarm_size', 'n_hiders']  # FIX: Changed from hiding_strategy
        missing_cols = [col for col in required_columns if col not in all_data.columns]

        if missing_cols:
            print(f"\nError: The loaded DataFrame is missing essential columns: {missing_cols}")
            print("This often happens if the 'combined_dataset.csv' file is old or malformed.")
            print(
                "Try setting 'force_rebuild=True' in the 'load_all_results(force_rebuild=True)' call in this script to regenerate it from raw files.")
            # We exit here because the plotting functions will fail
            sys.exit(1)

        # If check passes, proceed with printing and plotting
        print(f"\nSuccessfully loaded {len(all_data)} simulation results")
        print(f"Data shape: {all_data.shape}")
        print(f"Tactics: {sorted(all_data['tactic'].unique())}")
        print(f"Hiding strategies: {sorted(all_data['hide_strategy'].unique())}")  # FIX: Changed from hiding_strategy
        print(f"Swarm sizes: {sorted(all_data['swarm_size'].unique())}")
        print(f"N hiders: {sorted(all_data['n_hiders'].unique())}")

        # --- Generate all plots ---
        print("\n--- Generating All Plots ---")

        # Key metrics to analyze (using root names)
        key_metrics = ['steps', 'hider_frac_found', 'area_covered', 'taken_down']

        # # 1. Generate ORIGINAL FacetGrid Bar Plots
        # print("\n1. Creating original FacetGrid grouped bar plots...")
        # generate_grouped_bar_plots(all_data)
        #
        # # 2. Trend plots (from inspiration)
        # print("\n2. Creating trend plots...")
        # for metric in key_metrics:
        #     plot_trends_by_n_hiders(all_data, metric=metric)
        #
        # # 3. Heatmaps (from inspiration)
        # print("\n3. Creating heatmaps...")
        # for metric in key_metrics:
        #     plot_heatmap_by_tactic(all_data, metric=metric)

        # 4. Grouped bar charts (from inspiration)
        print("\n4. Creating grouped bar charts (alternative)...")
        for metric in key_metrics:
            plot_grouped_bars_with_errors(all_data, metric=metric, group_by='n_hiders')

        # # 5. Multi-metric comparison (from inspiration)
        # print("\n5. Creating multi-metric comparison...")
        # plot_multi_metric_comparison(all_data, metrics=key_metrics)
        #
        # # 6. Performance summary (from inspiration)
        # print("\n6. Creating performance summary...")
        # for metric in ['hider_frac_found', 'steps']:
        #     plot_performance_summary(all_data, metric=metric)

        print("\n--- All plots generated successfully! ---")

