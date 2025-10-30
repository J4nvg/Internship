import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binomtest
import re
import matplotlib.colors as mcolors

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
}





SUMMARY_FILENAME = './data/dataset/sim_results_dataset.csv'

FIXED_HIDING_STRATEGY = 'greedy'
FIXED_NUMBER_OF_HIDERS = 2

FIXED_HIDING_CANDIDATES = 5
FIXED_GRID_WIDTH = 20
FIXED_NUMBER_OF_RUNS = 100000

results = {}

df_all = pd.read_csv(SUMMARY_FILENAME)

df_filtered = df_all[
    (df_all['hide_strategy'] == FIXED_HIDING_STRATEGY) &
    (df_all['n_hiders'] == FIXED_NUMBER_OF_HIDERS) &
    (df_all['n_hider_candidates'] == FIXED_HIDING_CANDIDATES) &
    (df_all['grid_width'] == FIXED_GRID_WIDTH) &
    (df_all['runs'] == FIXED_NUMBER_OF_RUNS)
]

all_swarm_sizes = sorted(df_filtered['swarm_size'].unique())

for tactic_name in df_filtered['tactic'].unique():

    df_tactic = df_filtered[df_filtered['tactic'] == tactic_name]

    df_tactic = df_tactic.sort_values(by='swarm_size')

    results[tactic_name] = {
        'swarm_sizes': df_tactic['swarm_size'].values,
        'P':           df_tactic['all_found_mean'].values,
        'low':         df_tactic['all_found_ci_lower'].values,
        'high':        df_tactic['all_found_ci_upper'].values
    }

all_tactic_names = sorted(tactic_abbr_full.values())
colors_list = plt.cm.tab10(np.linspace(0, 1, len(all_tactic_names)))
tactic_colors = {tactic: color for tactic, color in zip(all_tactic_names, colors_list)}

print(all_tactic_names)

plt.figure(figsize=(10, 6))
ax = plt.gca()


for i, (tactic_name, data) in enumerate(results.items()):
    if not len(data['swarm_sizes']):
        print(f"{tactic_name} no data points")
        continue

    color = tactic_colors[tactic_name]

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
        color=color,
        label=f'_{tactic_name}_CI' # Underscore hides from legend
    )

ax.set_xlabel('Swarm Size', fontsize=12)
ax.set_ylabel('P(All Found)', fontsize=12)
title = (
    f'Probability of All Hiders Found vs. Swarm Size\n'
    f'Hiders={FIXED_NUMBER_OF_HIDERS}, HS={FIXED_HIDING_STRATEGY}, '
    f'Grid={FIXED_GRID_WIDTH}x{FIXED_GRID_WIDTH}'
)
ax.set_title(title, fontsize=14)

ax.legend(loc='upper left', title='Tactics')

ax.set_ylim(0, 1)

ax.set_xticks(all_swarm_sizes)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()

save_filename = (
    f'prob_all_found_vs_SwarmSize_'
    f'HS{FIXED_HIDING_STRATEGY}_H{FIXED_NUMBER_OF_HIDERS}.png'
)
plt.savefig(save_filename)
print(f"\nPlot saved to: {save_filename}")
plt.show()