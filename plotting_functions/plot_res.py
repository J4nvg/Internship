import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
from src.constants import tactic_abbr_full

tacts = []

for key,value in tactic_abbr_full.items():
    tacts.append(value)


cwd = os.getcwd()
current_folder = cwd.split("\\")[-1]

grid_size = [20]
swarm_size = [1, 5, 10]
hider_candidates = [5]
n_hiders = [1,2,3,4,5]

records = []


for tact in tacts:
    for g in grid_size:
        for s in swarm_size:
            for h in hider_candidates:
                path = f"./data/def_sim_res/{tact}_{g}_{s}_{h}.csv"
                if current_folder == "plotting_functions":
                    path = f"../data/def_sim_res/{tact}_{g}_{s}_{h}.csv"

                if not os.path.exists(path):
                    continue
                
                df = pd.read_csv(path, sep=r"\s+", index_col=0)
                
                records.append({
                    "Tactic": tact,
                    "Grid": g,
                    "Swarm_size": s,
                    "Hidercells": h,
                    "find_steps_mean": df.loc["find_steps", "mean"],
                    "find_steps_ci_low": df.loc["find_steps", "ci_lower"],
                    "find_steps_ci_up": df.loc["find_steps", "ci_upper"],
                    "find_steps_hw": df.loc["find_steps", "Half_width"],
                    "taken_down_mean": df.loc["taken_down", "mean"],
                    "taken_down_ci_low": df.loc["taken_down", "ci_lower"],
                    "taken_down_ci_up": df.loc["taken_down", "ci_upper"],
                    "taken_down_hw": df.loc["taken_down", "Half_width"],
                    "mean_distance_travelled_mean": df.loc["mean_distance_travelled", "mean"],
                    "mean_distance_travelled_ci_low": df.loc["mean_distance_travelled", "ci_lower"],
                    "mean_distance_travelled_ci_up": df.loc["mean_distance_travelled", "ci_upper"],
                    "mean_distance_travelled_hw": df.loc["mean_distance_travelled", "Half_width"],
                    "area_covered_mean": df.loc["area_covered", "mean"],
                    "area_covered_ci_low": df.loc["area_covered", "ci_lower"],
                    "area_covered_ci_up": df.loc["area_covered", "ci_upper"],
                    "area_covered_hw": df.loc["area_covered", "Half_width"],
                    "found_percentage": float(df.loc["Found", "min"].strip("%")),
                })



all_data = pd.DataFrame(records)
print(all_data.head())


def plot_metric_w_error_bars(metric):
    plt.figure(figsize=(12,6))
    if metric == 'found_percentage':
        ax = sns.barplot(data=all_data,x="Tactic",y=f"{metric}",hue="Swarm_size",errorbar=None,  )
        hue_cats = sorted(all_data["Swarm_size"].unique())
        num_hue = len(hue_cats)
        for i in range(num_hue):
            ax.bar_label(ax.containers[i], fontsize=10)
    else:
        sns.barplot(data=all_data,x="Tactic",y=f"{metric}_mean",hue="Swarm_size",errorbar=None,  )

        ax = plt.gca()
        x_cats = all_data["Tactic"].unique()
        hue_cats = sorted(all_data["Swarm_size"].unique())
        num_hue = len(hue_cats)
        bar_width = 0.8 / num_hue  


        for xi, tactic in enumerate(x_cats):
            for hi, swarm in enumerate(hue_cats):
                sub = all_data[(all_data["Tactic"] == tactic) & (all_data["Swarm_size"] == swarm)]
                if sub.empty:
                    continue
                y = sub[f"{metric}_mean"].values[0]
                hw = sub[f"{metric}_hw"].values[0]

                x = xi - 0.4 + bar_width/2 + hi*bar_width
                ax.errorbar(x, y, yerr=hw, fmt="none", c="black", capsize=3, lw=1)

        plt.xticks(rotation=45)
    plt.tight_layout()
    plt.title(f"{metric} by Tactic, and Swarm Size")
    plt.show()

# plot_metric_w_error_bars("find_steps")
# plot_metric_w_error_bars("area_covered")
# plot_metric_w_error_bars("taken_down")
# plot_metric_w_error_bars("mean_distance_travelled")
plot_metric_w_error_bars("found_percentage")


metrics = ["find_steps", "area_covered", "taken_down", "mean_distance_travelled"]

fig, axes = plt.subplots(2, 2, figsize=(18, 10))
axes = axes.flatten()

x_cats = all_data["Tactic"].unique()
hue_cats = sorted(all_data["Swarm_size"].unique())
num_hue = len(hue_cats)
bar_width = 0.8 / num_hue  

for ax, metric in zip(axes, metrics):
    sns.barplot(
        data=all_data,
        x="Tactic",
        y=f"{metric}_mean",
        hue="Swarm_size",
        errorbar=None,
        ax=ax,
        dodge=True
    )

    for xi, tactic in enumerate(x_cats):
        for hi, swarm in enumerate(hue_cats):
            sub = all_data[(all_data["Tactic"] == tactic) & (all_data["Swarm_size"] == swarm)]
            if sub.empty:
                continue
            y = sub[f"{metric}_mean"].values[0]
            hw = sub[f"{metric}_hw"].values[0]
            x = xi - 0.4 + bar_width/2 + hi*bar_width
            ax.errorbar(x, y, yerr=hw, fmt="none", c="black", capsize=3, lw=1)

    ax.set_title(f"{metric.replace('_', ' ').title()} by Tactic and Swarm Size")
    ax.tick_params(axis='x', rotation=25)

plt.tight_layout()
# plt.title(f"Metrics by Tactic, and Swarm Size on 20x20 grid")
plt.show()