import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib


path = Path.cwd() / "sim_logs" / "together_traverse_best_permutation.csv"

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
    try:
        # Use delim_whitespace=True because your CSV uses spaces, not commas
        # Use header=1 to skip the title row and use the second row as column names
        data = pd.read_csv(path, header=1)
    except FileNotFoundError:
        print(f"Error: The file was not found at {path}")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV: {e}")
        # This can happen if the file is being written to at the same time
        return

    # Get the x-axis values (simulation index)
    x = data['i']

    # Loop through each metric and its corresponding subplot axis
    for ax, metric in zip(axs, metrics_to_plot):
        # Clear the specific subplot for the new frame
        ax.cla()

        # Check if the metric column exists in the dataframe
        if metric not in data.columns:
            ax.set_title(f"'{metric}' not found")
            continue

        y_values = data[metric]

        # --- Special handling for the boolean 'found' column ---
        if metric == 'found':
            # Convert boolean (True/False) to integer (1/0) for plotting
            y_values = y_values.astype(int)
            # The running mean of 1s and 0s is the running success percentage
            ax.set_ylabel("Success Rate")
            ax.set_ylim(-0.1, 1.1)  # Set y-axis limits for percentage

        # Calculate the running mean for the current metric
        running_mean = y_values.expanding().mean()

        # Plot the raw data and the running mean on the current subplot
        ax.plot(x, y_values, label='Raw Value')
        ax.plot(x, running_mean, label='Running Mean', linestyle='--')

        # Set the title and legend for the subplot
        ax.set_title(f"Analysis of: {metric.replace('_', ' ').title()}")
        ax.legend(loc='upper left')
        ax.grid(True, linestyle='--', alpha=0.6)

    # Set common x-label for the bottom plots
    axes[-1].set_xlabel("Simulation Step (i)")
    axes[-2].set_xlabel("Simulation Step (i)")

    # Adjust layout to prevent titles and labels from overlapping
    fig.tight_layout(pad=2.0)


ani = FuncAnimation(fig, animate, fargs=(axes,), interval=500)

# Display the plot window
plt.show()