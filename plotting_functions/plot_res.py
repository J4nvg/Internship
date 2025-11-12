import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binomtest
import re


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

# Tactic abbreviation mapping
tactic_abbr_full = {
    "ttbp":"together_traverse_best_permutation",
    "dor":"divide_over_risks",
    "rndm":"random_walk",
    "hs":"horizontal_scan_traversal",
    "phs":"partitioned_horizontal_scan_traversal",
    "sp": "spiral_traversal_swarm",
    "lb": "lidbetter",
    "toq": "traverse_ordered_qa",
    "tpq":"traverse_p_qa",
    "dd":"discounted_distance",
    "ddr":"discounted_distance_reverse",
    "sl":"shared_list",
}


# ====================
# CONFIG
# ====================
HIDING_STRATEGIES = ['greedy', 'random', 'weighted']  # List of hiding strategies to plot
SWARM_SIZES = [1,5, 10]  # List of swarm sizes to plot
N_HIDERS_LIST = [2]  # List of number of hiders to plot
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
    colors_list = plt.cm.tab10(np.linspace(0, 1, len(all_tactic_names)))
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
    for p_dist in probability_distributions:
        print("Loading data...")
        df_all = pd.read_csv(get_file_name(p_dist,t="SUMMARY_FILENAME"))
        tactic_colors = get_tactic_colors()

        figures = []

        # Generate Probability vs Swarm Size plots
        print("\nGenerating Probability vs Swarm Size plots...")
        for hiding_strategy in HIDING_STRATEGIES:
            for n_hiders in N_HIDERS_LIST:
                print(f"  - HS={hiding_strategy}, Hiders={n_hiders}")
                fig = plot_prob_vs_swarm_size(df_all, hiding_strategy, n_hiders, tactic_colors, p_dist)
                if fig:
                    figures.append(fig)

        # Generate Probability vs Time plots
        print("\nGenerating Probability vs Time plots...")
        for hiding_strategy in HIDING_STRATEGIES:
            for swarm_size in SWARM_SIZES:
                for n_hiders in N_HIDERS_LIST:
                    print(f"  - HS={hiding_strategy}, Swarm={swarm_size}, Hiders={n_hiders}")
                    fig = plot_prob_vs_time(hiding_strategy, swarm_size, n_hiders, tactic_colors,p_dist)
                    if fig:
                        figures.append(fig)

        print(f"\n{'=' * 50}")
        print(f"Total plots generated: {len(figures)}")
        print(f"{'=' * 50}")
        print("\nAll plots are now open. Close windows to exit.")
        plt.show()


if __name__ == "__main__":
    main()