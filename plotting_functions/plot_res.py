import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binomtest
import matplotlib.patches as patches
import re
import seaborn as sns

# Tactic abbreviation mapping
tactic_abbr_full = {
    "ttbp":"together_traverse_best_permutation",

    "dor":"divide_over_risks",

    # "rndm":"random_walk",

    "hs":"horizontal_scan_traversal",

    "phs":"partitioned_horizontal_scan_traversal",

    # "sp": "spiral_traversal_swarm",

    "lb": "lidbetter",

    "toq": "traverse_ordered_qa",

    "tpq":"traverse_p_qa",

    # "dd":"discounted_distance",

    # "ddr":"discounted_distance_reverse",

    "sl":"shared_list",
}



def create_performance_heatmap(data,
                               distribution_key,
                               swarm_size,
                               metric='P',
                               figsize=(6, 6),
                               title=None,
                               annotate=True,
                               fmt='.3f',
                               tactic_order=None,
                               ax=None,
                               show_xlabel=True,
                               show_xticklabels=True,
                                anchor_rows = False,
                               box_highest = False,
                               ):
    """
    Creates a heatmap of performance (metric P) for hiding strategy vs search tactic
    for a given swarm size and probability distribution.
    """

    # Extract data for one probability distribution
    if distribution_key not in data:
        raise ValueError(f"Distribution '{distribution_key}' not found in data.")
    dist_data = data[distribution_key]

    hiding_strategies = list(dist_data.keys())

    first_hs_list = dist_data[hiding_strategies[0]]

    available_tactics = [t[0] for t in first_hs_list]

    # Force an alphabetical sort for the Master Column Order
    master_tactic_names = sorted(available_tactics)

    # Build performance matrix
    performance_matrix = []
    for hs in hiding_strategies:
        hs_data_map = dict(dist_data[hs])

        row_vals = []

        for tactic_name in master_tactic_names:
            if tactic_name not in hs_data_map:
                raise ValueError(f"Tactic {tactic_name} missing in strategy {hs}")

            stats = hs_data_map[tactic_name]
            swarm_sizes = stats['swarm_sizes']

            if swarm_size not in swarm_sizes:
                raise ValueError(f"Swarm size {swarm_size} not in {tactic_name} for hiding strategy {hs}")

            swarm_idx = np.where(swarm_sizes == swarm_size)[0][0]
            val = stats[metric][swarm_idx]
            row_vals.append(val)

        performance_matrix.append(row_vals)

    performance_matrix = np.array(performance_matrix)
    tactic_names = master_tactic_names


    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Row wise normalisation
    row_mins = performance_matrix.min(axis=1, keepdims=True)
    row_maxs = performance_matrix.max(axis=1, keepdims=True)
    divisors = row_maxs - row_mins
    divisors[divisors == 0] = 1

    color_matrix = (performance_matrix - row_mins) / divisors
    if anchor_rows:
        sns.heatmap(color_matrix, #normalised rows
                    annot=performance_matrix, # original data
                    fmt=fmt,
                    xticklabels=tactic_names,
                    yticklabels=hiding_strategies,
                    linewidths=0.25,
                    linecolor='gray',
                    cmap='vlag',
                    ax=ax,
                    cbar=False)
    else:
        # Plot heatmap
        sns.heatmap(performance_matrix,
                    annot=annotate,
                    fmt=fmt,
                    xticklabels=tactic_names,
                    yticklabels=hiding_strategies,
                    # cbar_kws={'label': cbar_label},
                    linewidths=0.25,
                    linecolor='gray',
                    cmap='vlag',

                    ax=ax,
                    cbar=True)

    rows, cols = performance_matrix.shape
    if box_highest:
        for r in range(rows):
            row_values = performance_matrix[r, :]

            # format all values in the row to strings to ensure matching rounding logic
            row_strs = [f"{x:.3f}" for x in row_values]

            # Find the max value based on the actual numbers, then format it
            max_val_str = f"{np.max(row_values):.3f}"

            # Find all indices where the string representation matches
            max_idxs = [i for i, x in enumerate(row_strs) if x == max_val_str]

            for c in max_idxs:
                rect = patches.Rectangle((c, r), 1, 1,
                                         linewidth=3,
                                         edgecolor='#32CD32',
                                         facecolor='none')
                ax.add_patch(rect)


    if show_xlabel:
        ax.set_xlabel('Search Tactic', fontweight='bold')
    else:
        ax.set_xlabel('')  # Remove x-label if not needed

    if show_xticklabels:
        ax.set_xticklabels(tactic_names, rotation=30, ha='right')
    else:
        ax.set_xticklabels([])  # Remove x-tick labels
    ax.set_ylabel('Hiding Strategy', fontweight='bold')
    ax.tick_params(axis='y', labelrotation=30)

    title = title or f'P(ALL FOUND) (Swarm={swarm_size})'

    if anchor_rows:
        ax.set_title(f"{title}\n(Colors normalized per row)", fontsize=10, pad=20)
    else:
        ax.set_title(title, fontsize=10, pad=20)

    plt.tight_layout()

    return fig, ax


def generate_latex_table(results_object, caption,FIXED_HIDING_STRATEGY):
    """
    Generates a formatted LaTeX table string from a results object.

    Args:
        results_object (list): A list of tuples, where each tuple is
            (tactic_name, data_dict). data_dict contains 'P', 'low', 'high'
            as lists or numpy arrays.
        caption (str): The LaTeX caption for the table.
        label (str): The LaTeX label for the table.
        tactic_order (list, optional): A list of tactic names in the order
            they should appear in the table. If None, it will default to
            a pre-defined order based on the example.

    Returns:
        str: A fully formatted LaTeX table as a string.
    """

    label = f"tab:swarm_performance_{FIXED_HIDING_STRATEGY}"

    # This is the order of tactics as seen in your example tables.
    # We use this to ensure the rows are in the correct order.
    tactic_order = [tup[0] for tup in results_object]

    # Convert the input list of tuples into a dictionary for easy lookup
    data_dict = dict(results_object)

    # Find the maximum 'P' value for each column (swarm size)
    # We initialize with negative infinity to ensure any value is larger
    max_p = [-float('inf'), -float('inf'), -float('inf')]
    num_cols = 3 # Assumes 3 swarm sizes (1, 5, 10)

    for tactic_name in tactic_order:
        if tactic_name in data_dict:
            p_values = data_dict[tactic_name]['P']
            for i in range(num_cols):
                if p_values[i] > max_p[i]:
                    max_p[i] = p_values[i]

    # Start building the LaTeX string
    latex_lines = []
    latex_lines.append(r"\begin{table}[h]")
    latex_lines.append(r"\centering")
    latex_lines.append(r"\begin{tabular}{lccc}")
    latex_lines.append(r"\hline")
    latex_lines.append(r"\textbf{Tactic Name} & \textbf{Swarm size 1} & \textbf{Swarm size 5} & \textbf{Swarm size 10} \\")
    latex_lines.append(r"\hline")

    # Iterate through the tactics in the specified order to build rows
    for tactic_name in tactic_order:
        if tactic_name in data_dict:
            data = data_dict[tactic_name]
            P = data['P']
            low = data['low']
            high = data['high']

            # Escape underscores in tactic names for LaTeX
            latex_tactic_name = tactic_name.replace('_', r'\_')

            row_cols = [latex_tactic_name]

            # Format each column value
            for i in range(num_cols):
                val_str = f"{P[i]:.3f} [{low[i]:.3f}, {high[i]:.3f}]"

                # Add \textbf if this is the max value in the column
                if P[i] == max_p[i]:
                    row_cols.append(r"\textbf{" + val_str + r"}")
                else:
                    row_cols.append(val_str)

            # Join all columns with '&' and add the LaTeX line ending
            latex_lines.append(" & ".join(row_cols) + r" \\")

    # Add the table footer
    latex_lines.append(r"\hline")
    latex_lines.append(r"\end{tabular}")
    # Use f-string to insert the caption and label
    latex_lines.append(rf"\caption{{{caption}}}")
    latex_lines.append(rf"\label{{{label}}}")
    latex_lines.append(r"\end{table}")

    # Join all lines with a newline character and return
    return "\n".join(latex_lines)


RESULTS_DICT = {}


Pi_DICT = {
    # Initial settings, before adding multiple sets
                # 1       2       3       4       5       6
    "SUCCESS_PROBABILITIES_INITIAL":
        {"p": [   1/3,    2/3,    3/4,    4/5,    9/10,   95/100],
         "WITH_REPLACEMENT": True
         },

    "SUCCESS_PROBABILITIES_HIGH_VAR":
        {
                # 1       2       3       4       5
        "p": [  0.10,   0.30,   0.60,   0.80,   0.95],
        "WITH_REPLACEMENT": False
        },

    "SUCCESS_PROBABILITIES_LOW_VAR":
                # 1       2       3       4       5
        {"p": [  0.60,   0.62,   0.64,   0.66,   0.68],
         "WITH_REPLACEMENT": False
         },

    "SUCCESS_PROBABILITIES_SKEWED":
                # 1       2       3       4       5
        {"p": [  0.60,    0.62,   0.64,   0.66,   0.10],
         "WITH_REPLACEMENT": False
         },
}




# ====================
# CONFIG
# ====================
HIDING_STRATEGIES = ['greedy', 'random', 'weighted']  # List of hiding strategies to plot
SWARM_SIZES = [1,5, 10]  # List of swarm sizes to plot
N_HIDERS_LIST = [1]  # List of number of hiders to plot
PLOT_DIR = os.path.join("..", "plots")
os.makedirs(PLOT_DIR, exist_ok=True)
probability_distributions = Pi_DICT.keys()


# Fixed parameters
FIXED_HIDING_CANDIDATES = 5
FIXED_GRID_WIDTH = 20
FIXED_NUMBER_OF_RUNS = 100000

# For time-based plots
T_MIN = 0
T_MAX = 1000
T_STEP = 10
T_values = np.arange(T_MIN, T_MAX + T_STEP, T_STEP)

# File paths
def get_file_name(p_dist, t="SUMMARY_FILENAME"):
    if t == "SUMMARY_FILENAME":
        try:
            return f"../data/dataset/{p_dist}/sim_results_dataset.csv"
        except:
            raise Exception(f"No file named ../data/dataset/{p_dist}/sim_results_dataset.csv")
    else:
        try:
            return f"../data/sim_logs/{p_dist}/"
        except:
            raise Exception(f"No folder named ../data/sim_logs/{p_dist}/")


# ====================
# HELPER FUNCTIONS
# ====================

def get_tactic_colors():
    """Generate consistent colors for all tactics"""
    all_tactic_names = sorted(tactic_abbr_full.values())
    colors_list = plt.cm.tab20(np.linspace(0, 1, len(all_tactic_names)))
    return {tactic: color for tactic, color in zip(all_tactic_names, colors_list)}


def plot_prob_vs_swarm_size(df_all, hiding_strategy, n_hiders, tactic_colors,p_dist):
    """Create plot: Probability vs Swarm Size"""
    df_filtered = df_all[
        (df_all['hide_strategy'] == hiding_strategy) &
        (df_all['n_hiders'] == n_hiders) &
        (df_all['n_hider_candidates'] == FIXED_HIDING_CANDIDATES) &
        (df_all['grid_width'] == FIXED_GRID_WIDTH) &
        (df_all['runs'] == FIXED_NUMBER_OF_RUNS)
        ]

    if df_filtered.empty:
        print(f"No data for HS={hiding_strategy}, Hiders={n_hiders}")
        return None

    all_swarm_sizes = sorted(df_filtered['swarm_size'].unique())
    results = {}

    for tactic_name in df_filtered['tactic'].unique():
        df_tactic = df_filtered[df_filtered['tactic'] == tactic_name]
        df_tactic = df_tactic.sort_values(by='swarm_size')

        results[tactic_name] = {
            'swarm_sizes': df_tactic['swarm_size'].values,
            'P': df_tactic['all_found_mean'].values,
            'low': df_tactic['all_found_ci_lower'].values,
            'high': df_tactic['all_found_ci_upper'].values
        }

    sorted_results = sorted(
        results.items(),
        key=lambda item: item[1]['P'][-1] if len(item[1]['P']) > 0 else -1,
        reverse=True
    )

    print(sorted_results)

    if p_dist not in RESULTS_DICT:
        RESULTS_DICT[p_dist] = {}
    RESULTS_DICT[p_dist][hiding_strategy] = sorted_results


    # caption = f"Probability that all hiders were found, comparison across different swarm sizes for \\textbf{{hiding_strategy {hiding_strategy}}}, {n_hiders} hiders, 5 possible hiding spots and 20 x 20 grid and Probability distribution {p_dist}."
    # latex_output = generate_latex_table(sorted_results, caption,hiding_strategy)
    # print("\n", "#" *5 , " Latex Table ", "#" * 5, "\n")
    # print(latex_output)
    # print("\n \n")


    fig = plt.figure(figsize=(10, 6))
    ax = plt.gca()

    for tactic_name, data in sorted_results:
        if not len(data['swarm_sizes']):
            continue

        color = tactic_colors.get(tactic_name, 'gray')

        ax.plot(
            data['swarm_sizes'],
            data['P'],
            label=tactic_name,
            color=color,
            linewidth=2,
            marker='o',
            markersize=8
        )

        ax.fill_between(
            data['swarm_sizes'],
            data['low'],
            data['high'],
            alpha=0.15,
            color=color
        )

    ax.set_xlabel('Swarm Size', fontsize=12)
    ax.set_ylabel('P(All Found)', fontsize=12)
    p_dist_title = p_dist.lower()
    title = (
        f'Probability of All Hiders Found vs. Swarm Size\n'
        f'Hiders={n_hiders}, HS={hiding_strategy}, '
        f'Grid={FIXED_GRID_WIDTH}x{FIXED_GRID_WIDTH}'
        f'{p_dist_title}'
    )
    ax.set_title(title, fontsize=14)
    ax.legend(loc='upper left', title='Tactics')
    ax.set_ylim(0, 1)
    ax.set_xticks(all_swarm_sizes)
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot_dir = os.path.join(f"{PLOT_DIR}", f"{p_dist}", f"H{N_HIDERS_LIST[0]}")
    os.makedirs(plot_dir, exist_ok=True)
    plt.savefig(os.path.join(plot_dir, f"psucces_givenswarmsize_hiders_{n_hiders}_hidingstrat_{hiding_strategy}.svg"),bbox_inches="tight")

    return fig


def plot_prob_vs_time(hiding_strategy, swarm_size, n_hiders, tactic_colors,p_dist=None):
    """Create plot: Probability vs Time (Stepslimit)"""
    filename_pattern = re.compile(
        r"T-(.+)"
        r"-W-(\d+)"
        r"-HS-(.+)"
        r"-D-(\d+)"
        r"-C-(\d+)"
        r"-H-(\d+)"
        r"-RUNS-(\d+)\.csv"
    )

    results = {}
    sim_logs = ""


    sim_logs = get_file_name(f"{p_dist}", "sim_logs")

    for filename in os.listdir(sim_logs):
        if not filename.endswith('.csv'):
            continue

        match = filename_pattern.match(filename)
        if not match:
            continue

        tactic = match.group(1)
        width = int(match.group(2))
        hs = match.group(3)
        swarm = int(match.group(4))
        candidates = int(match.group(5))
        hiders = int(match.group(6))
        runs = int(match.group(7))

        if (swarm == swarm_size and
                hs == hiding_strategy and
                candidates == FIXED_HIDING_CANDIDATES and
                hiders == n_hiders and
                width == FIXED_GRID_WIDTH and
                runs == FIXED_NUMBER_OF_RUNS):

            df = pd.read_csv(os.path.join(sim_logs, filename), header=0, sep=r'\s+')
            successful_runs = df[df['all_found'] == True]

            probabilities = []
            ci_low = []
            ci_high = []

            for T in T_values:
                k_success_within_T = (successful_runs['steps'] <= T).sum()
                result = binomtest(k=k_success_within_T, n=FIXED_NUMBER_OF_RUNS)

                probabilities.append(result.statistic)
                ci = result.proportion_ci()
                ci_low.append(ci.low)
                ci_high.append(ci.high)

            results[tactic] = {
                'T': T_values,
                'P': probabilities,
                'low': ci_low,
                'high': ci_high
            }

    if not results:
        print(f"No time data for HS={hiding_strategy}, Swarm={swarm_size}, Hiders={n_hiders}")
        return None

    sorted_results = sorted(
        results.items(),
        key=lambda item: item[1]['P'][-1],
        reverse=True
    )

    fig = plt.figure(figsize=(10, 6))
    ax = plt.gca()

    for tactic_name, data in sorted_results:
        color = tactic_colors.get(tactic_name, 'gray')

        ax.plot(
            data['T'],
            data['P'],
            label=tactic_name,
            color=color,
            linewidth=2
        )

        ax.fill_between(
            data['T'],
            data['low'],
            data['high'],
            alpha=0.2,
            color=color
        )

    ax.set_xlabel('Stepslimit T', fontsize=12)
    ax.set_ylabel('P(All Found | steps $\leq$ T)', fontsize=12)
    p_dist_title = p_dist.lower()
    title = (
        f'Probability of All Hiders Found vs. Stepslimit (T)\n'
        f'Swarm Size={swarm_size}, Hiders={n_hiders}, '
        f'Grid={FIXED_GRID_WIDTH}x{FIXED_GRID_WIDTH}, HS={hiding_strategy}'
        f'{p_dist_title}'
    )
    ax.set_title(title, fontsize=14)
    ax.legend(loc='lower right', title='Tactics')
    ax.set_ylim(0, 1)
    ax.set_xlim(T_MIN, T_MAX)
    ax.set_xticks(np.arange(T_MIN, T_MAX, 100))
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plot_dir = os.path.join(f"{PLOT_DIR}", f"{p_dist}", f"H{N_HIDERS_LIST[0]}")
    os.makedirs(plot_dir, exist_ok=True)
    plt.savefig(os.path.join(plot_dir, f"psucces_giventime_swarmsize_{swarm_size}_hiders_{n_hiders}_hidingstrat_{hiding_strategy}.svg"),bbox_inches="tight")
    return fig


# ====================
# MAIN EXECUTION
# ====================

def main():
    # Load data
    to_plot_tactics = list(tactic_abbr_full.values())

    for p_dist in probability_distributions:
        if p_dist == "SUCCESS_PROBABILITIES_INITIAL":
            continue
        print("Loading data...")
        df_all = pd.read_csv(get_file_name(p_dist,t="SUMMARY_FILENAME"))
        tactic_colors = get_tactic_colors()
        df_all = df_all[df_all['tactic'].isin(to_plot_tactics)]
        figures = []

        # Generate Probability vs Swarm Size plots
        print("\nGenerating Probability vs Swarm Size plots...")
        for hiding_strategy in HIDING_STRATEGIES:
            for n_hiders in N_HIDERS_LIST:
                print(f"  - HS={hiding_strategy}, Hiders={n_hiders}")
                fig = plot_prob_vs_swarm_size(df_all, hiding_strategy, n_hiders, tactic_colors, p_dist)
                if fig:
                    # figures.append(fig)
                    pass

        # Generate Probability vs Time plots
        # print("\nGenerating Probability vs Time plots...")
        # for hiding_strategy in HIDING_STRATEGIES:
        #     for swarm_size in SWARM_SIZES:
        #         for n_hiders in N_HIDERS_LIST:
        #             print(f"  - HS={hiding_strategy}, Swarm={swarm_size}, Hiders={n_hiders}")
        #             fig = plot_prob_vs_time(hiding_strategy, swarm_size, n_hiders, tactic_colors,p_dist)
        #             if fig:
        #                 figures.append(fig)

        print(f"\n{'=' * 50}")
        print(f"Total plots generated: {len(figures)}")
        print(f"{'=' * 50}")
        print("\nAll plots are now open. Close windows to  exit.")
    plt.show()

    # SUCCESS_PROBABILITIES_HIGH_VAR | SUCCESS_PROBABILITIES_LOW_VAR | SUCCESS_PROBABILITIES_SKEWED

    # dist_key = "SUCCESS_PROBABILITIES_SKEWED"

    for dist_key in probability_distributions:
        if dist_key == "SUCCESS_PROBABILITIES_INITIAL":
            continue


        print("\nGenerating stacked heatmap figure...")
        swarm_sizes_to_plot = [10, 5,1]
        num_plots = len(swarm_sizes_to_plot)

        fig, axes = plt.subplots(nrows=num_plots,
                                 ncols=1,
                                 figsize=(12,10),  # Taller figure (e.g., 6 inches per plot)
                                 sharex=True)

        if num_plots == 1:
            axes = [axes]

        # Loop through the axes and swarm sizes to create each plot
        for i, swarm_size in enumerate(swarm_sizes_to_plot):
            ax = axes[i]  # Get the current subplot axis

            # Determine if this is the bottom-most plot
            is_last_plot = (i == num_plots - 1)

            # Call the modified function
            create_performance_heatmap(
                data=RESULTS_DICT,
                distribution_key=dist_key,
                swarm_size=swarm_size,
                ax=ax,
                show_xlabel=is_last_plot,
                show_xticklabels=is_last_plot,
                anchor_rows=True,
                box_highest=True
            )

        # Add an overall title to the entire figure
        fig.suptitle(f'H={N_HIDERS_LIST[0]} Stacked P(All found) per search policy and hiding strategy Heatmaps ({dist_key})', fontsize=12)

        fig.tight_layout(rect=[0, 0.03, 1, 0.98])

        # Save and show the final stacked figure
        file_path = os.path.join("..", "plots", f"{dist_key}",f"H{N_HIDERS_LIST[0]}",f"stacked_heatmap_figure_{dist_key}.svg")
        plt.savefig(file_path, bbox_inches='tight')
        plt.show()





if __name__ == "__main__":
    main()