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


fig, axes = plt.subplots(3, 2, figsize=(15, 10), sharex=True)

axes = axes.flatten()


def animate(i, axs):
    """
    This function is called for each frame of the animation.
    It reads the data and updates all subplots.
    """

    data = pd.read_csv(path, header=1)
    x = data['i']

    for ax, metric in zip(axs, metrics_to_plot):
        # Clear the specific subplot for the new frame
        ax.cla()

        if metric not in data.columns:
            ax.set_title(f"'{metric}' not found")
            continue

        y_values = data[metric]

        if metric == 'found':
            # Convert boolean (True/False) to integer (1/0) for plotting
            y_values = y_values.astype(int)
            ax.set_ylabel("Success Rate")
            ax.set_ylim(-0.1, 1.1)

        running_mean = y_values.expanding().mean()

        ax.plot(x, y_values, label='Raw Value')
        ax.plot(x, running_mean, label='Running Mean', linestyle='--')

        ax.set_title(f"Analysis of: {metric.replace('_', ' ').title()}")
        ax.legend(loc='upper left')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_xlabel("Simulation Step (i)")


    fig.tight_layout(pad=2.0)


ani = FuncAnimation(fig, animate, fargs=(axes,), interval=500)

# Display the plot window
plt.show()