import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib
import argparse



parser = argparse.ArgumentParser(description="Specify Simulation Tactic")

parser.add_argument("--tactic", required=True, type=str, choices=["ttbp", "rndm", "hs", "vs", "dor", "phs"],
                    help="Tactic to use")
args = parser.parse_args()

tactic_map = {
    "ttbp":"together_traverse_best_permutation",
    "dor":"divide_over_risks",
    "rndm":"random_walk",
    "hs":"horizontal_scan_traversal",
    "phs":"partitioned_horizontal_scan_traversal",
    "vs":"vertical_scan_traversal",
}

path = Path.cwd() / "sim_logs" / f"{tactic_map[args.tactic]}.csv"

metrics_to_plot = [
    'steps',
    'found',
    'taken_down',
    'frac_area_covered',
    'mean_distance_travelled',
    'total_distance_covered'
]


# fig, axes = plt.subplots(3, 2, figsize=(15, 10), sharex=True)

# axes = axes.flatten()

def animate(i):
    data = pd.read_csv(path, header=1)
    x = data['i']
    y1 = data['frac_area_covered']

    running_mean = y1.expanding().mean()
    plt.cla()

    plt.plot(x, y1, label='Fraction of Area Covered')
    plt.plot(x, running_mean, label='Running Mean of Area Covered', linestyle='--')

    plt.legend(loc='upper left')

plt.tight_layout()
ani = FuncAnimation(plt.gcf(), animate, interval=1000)
plt.tight_layout()
plt.show()