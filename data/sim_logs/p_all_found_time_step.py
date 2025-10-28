import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binomtest
import matplotlib.colors as mcolors
tactic_abbr_full = {
    "ttbp":"together_traverse_best_permutation",
    "dor":"divide_over_risks",
    "rndm":"random_walk",
    "hs":"horizontal_scan_traversal",
    "phs":"partitioned_horizontal_scan_traversal",
    # "vs":"vertical_scan_traversal",
    "sp": "spiral_traversal_swarm",
    "lb": "lidbetter",
    "toq": "traverse_ordered_qa",
    "tpq":"traverse_weighted_qa",
    "dd":"discounted_distance",
}

FIXED_SWARM_SIZE = 10
FIXED_HIDING_STRATEGY = 'greedy'
FIXED_NUMBER_OF_HIDERS = 2

FIXED_HIDING_CANDIDATES = 5
FIXED_GRID_WIDTH = 20

FIXED_NUMBER_OF_RUNS = 100000 


T_MIN = 0
T_MAX = 4000
T_STEP = 10 
T_values = np.arange(T_MIN, T_MAX + T_STEP, T_STEP)

# T-{TACTIC}-W-{GRIDWIDTH}-HS-{HidingStrategy}-D-{Swarmsize}-C-{HidingCandidates}-H-{NumberOfHiders}-RUNS-{NumberOfRuns}.csv
filename_pattern = re.compile(
    r"T-(.+)"                  # Group 1: TACTIC
    r"-W-(\d+)"                # Group 2: GRIDWIDTH
    r"-HS-(.+)"                # Group 3: HidingStrategy
    r"-D-(\d+)"                # Group 4: Swarmsize
    r"-C-(\d+)"                # Group 5: HidingCandidates
    r"-H-(\d+)"                # Group 6: NumberOfHiders
    r"-RUNS-(\d+)\.csv"        # Group 7: NumberOfRuns
)


results = {}
tactic_files_found = []

for filename in os.listdir('.'):
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

    if (swarm == FIXED_SWARM_SIZE and
        hs == FIXED_HIDING_STRATEGY and
        candidates == FIXED_HIDING_CANDIDATES and
        hiders == FIXED_NUMBER_OF_HIDERS and
        width == FIXED_GRID_WIDTH and
        runs == FIXED_NUMBER_OF_RUNS):
        
        tactic_files_found.append(filename)

        df = pd.read_csv(filename, header=0, sep='\s+')

        successful_runs = df[df['all_hiders_found'] == True]

        probabilities = []
        ci_low = []
        ci_high = []

        for T in T_values:
            # Count successes *within* the step limit T
            # We filter the *already successful* runs for speed
            k_success_within_T = (successful_runs['steps'] <= T).sum()
            

            # k = number of successes (found all within T steps)

            result = binomtest(k=k_success_within_T, n=FIXED_NUMBER_OF_RUNS)
            
            probabilities.append(result.statistic)
            ci = result.proportion_ci()
            ci_low.append(ci.low)
            ci_high.append(ci.high)

        # Store results for this tactic
        results[tactic] = {
            'T': T_values,
            'P': probabilities,
            'low': ci_low,
            'high': ci_high
        }


all_tactic_names = sorted(tactic_abbr_full.values())
colors_list = plt.cm.tab10(np.linspace(0, 1, len(all_tactic_names)))
tactic_colors = {tactic: color for tactic, color in zip(all_tactic_names, colors_list)}

plt.figure(figsize=(10, 6))
ax = plt.gca()

for i, (tactic_name, data) in enumerate(results.items()):
    color = tactic_colors[tactic_name]
    
    # Plot the main probability line
    ax.plot(
        data['T'], 
        data['P'], 
        label=tactic_name, 
        color=color,
        linewidth=2
    )
    
    # Plot the confidence interval as a filled area
    ax.fill_between(
        data['T'], 
        data['low'], 
        data['high'], 
        alpha=0.2, 
        color=color,
        label=f'_{tactic_name}_CI' # Underscore hides from legend
    )

ax.set_xlabel('Stepslimit T', fontsize=12)
ax.set_ylabel('P(All Found | steps $\leq$ T)', fontsize=12)
title = (
    f'Probability of All Hiders Found vs. Stepslimit (T)\n'
    f'Swarm Size={FIXED_SWARM_SIZE}, Hiders={FIXED_NUMBER_OF_HIDERS}, '
    f'Grid={FIXED_GRID_WIDTH}x{FIXED_GRID_WIDTH}, HS={FIXED_HIDING_STRATEGY}'
)
ax.set_title(title, fontsize=14)
ax.legend(loc='lower right', title='Tactics')
ax.set_ylim(0, 1) 
ax.set_xlim(T_MIN, T_MAX)
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig(f'prob_all_hiders_found_vs_T_D{FIXED_SWARM_SIZE}_HS{FIXED_HIDING_STRATEGY}.png')
print(f"Plot saved to: prob_all_hiders_found_vs_T_D{FIXED_SWARM_SIZE}_HS{FIXED_HIDING_STRATEGY}.png")
plt.show()