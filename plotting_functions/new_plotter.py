import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
import glob
from pathlib import Path

# Configuration
sns.set_palette("husl")
DATA_PATH = "./data/sim_results"

# Parse filename function
def parse_filename(filename):
    """
    Parse filename format:
    T-{tactic}-W-{width}-HS-{hiding_strategy}-D-{swarm_size}-C-{n_hider_candidates}-H-{n_hiders}-RUNS-{runs}.csv
    """
    parts = filename.replace('.csv', '').split('-')
    return {
        'tactic': parts[1],
        'width': int(parts[3]),
        'hiding_strategy': parts[5],
        'swarm_size': int(parts[7]),
        'n_hider_candidates': int(parts[9]),
        'n_hiders': int(parts[11]),
        'runs': int(parts[13])
    }

# Load all data
def load_all_results(data_path=DATA_PATH):
    """Load all CSV files and combine into a single DataFrame"""
    records = []
    
    csv_files = glob.glob(os.path.join(data_path, "*.csv"))
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        params = parse_filename(filename)
        
        df = pd.read_csv(filepath, sep=r"\s+", index_col=0)
        
        record = {
            "tactic": params['tactic'],
            "hiding_strategy": params['hiding_strategy'],
            "swarm_size": params['swarm_size'],
            "n_hiders": params['n_hiders'],
            "n_hider_candidates": params['n_hider_candidates'],
            "width": params['width'],
            "runs": params['runs'],
        }
        
        # Add metrics
        metrics = ['find_steps', 'taken_down', 'area_covered', 
                   'mean_distance_travelled', 'total_distance_covered', 'hider_frac_found']
        
        for metric in metrics:
            if metric in df.index:
                record[f"{metric}_mean"] = df.loc[metric, "mean"]
                record[f"{metric}_ci_low"] = df.loc[metric, "ci_lower"]
                record[f"{metric}_ci_up"] = df.loc[metric, "ci_upper"]
                record[f"{metric}_hw"] = df.loc[metric, "Half_width"]
        
        # Handle 'Found' percentage
        if 'Found' in df.index:
            found_val = df.loc["Found", "min"]
            record["found_percentage"] = float(str(found_val).strip("%"))
        
        records.append(record)
    
    return pd.DataFrame(records)

# Plot 1: Line plots showing trends across n_hiders
def plot_trends_by_n_hiders(data, metric='find_steps'):
    """Line plot: metric vs n_hiders, faceted by hiding strategy, colored by swarm size"""
    hiding_strategies = sorted(data['hiding_strategy'].unique())
    
    fig, axes = plt.subplots(1, len(hiding_strategies), figsize=(18, 5), sharey=True)
    if len(hiding_strategies) == 1:
        axes = [axes]
    
    for ax, hiding_strat in zip(axes, hiding_strategies):
        subset = data[data['hiding_strategy'] == hiding_strat]
        
        for tactic in sorted(subset['tactic'].unique()):
            tactic_data = subset[subset['tactic'] == tactic]
            
            for swarm in sorted(tactic_data['swarm_size'].unique()):
                swarm_data = tactic_data[tactic_data['swarm_size'] == swarm].sort_values('n_hiders')
                
                ax.plot(swarm_data['n_hiders'], swarm_data[f'{metric}_mean'], 
                       marker='o', label=f"{tactic} (S={swarm})", alpha=0.7)
                ax.fill_between(swarm_data['n_hiders'], 
                               swarm_data[f'{metric}_ci_low'], 
                               swarm_data[f'{metric}_ci_up'], alpha=0.2)
        
        ax.set_title(f"Hiding: {hiding_strat}")
        ax.set_xlabel("Number of Hiders")
        ax.grid(True, alpha=0.3)
    
    axes[0].set_ylabel(metric.replace('_', ' ').title())
    axes[-1].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    plt.suptitle(f"{metric.replace('_', ' ').title()} vs Number of Hiders", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.show()

# Plot 2: Heatmap for each tactic
def plot_heatmap_by_tactic(data, metric='find_steps'):
    """Heatmap: swarm_size vs n_hiders, faceted by tactic and hiding strategy"""
    tactics = sorted(data['tactic'].unique())
    hiding_strategies = sorted(data['hiding_strategy'].unique())
    
    fig, axes = plt.subplots(len(hiding_strategies), len(tactics), 
                             figsize=(4*len(tactics), 4*len(hiding_strategies)))
    
    if len(hiding_strategies) == 1:
        axes = axes.reshape(1, -1)
    if len(tactics) == 1:
        axes = axes.reshape(-1, 1)
    
    for i, hiding_strat in enumerate(hiding_strategies):
        for j, tactic in enumerate(tactics):
            subset = data[(data['tactic'] == tactic) & 
                         (data['hiding_strategy'] == hiding_strat)]
            
            pivot = subset.pivot_table(values=f'{metric}_mean', 
                                      index='swarm_size', 
                                      columns='n_hiders')
            
            sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', 
                       ax=axes[i, j], cbar_kws={'label': metric})
            axes[i, j].set_title(f"{tactic} | {hiding_strat}")
            axes[i, j].set_xlabel("Number of Hiders")
            axes[i, j].set_ylabel("Swarm Size")
    
    plt.suptitle(f"{metric.replace('_', ' ').title()} Heatmap", fontsize=16, y=1.00)
    plt.tight_layout()
    plt.show()

# Plot 3: Grouped bar chart with error bars
def plot_grouped_bars_with_errors(data, metric='find_steps', group_by='n_hiders'):
    """Bar chart comparing tactics, grouped by n_hiders or swarm_size"""
    hiding_strategies = sorted(data['hiding_strategy'].unique())
    
    fig, axes = plt.subplots(1, len(hiding_strategies), figsize=(20, 6), sharey=True)
    if len(hiding_strategies) == 1:
        axes = [axes]
    
    for ax, hiding_strat in zip(axes, hiding_strategies):
        subset = data[data['hiding_strategy'] == hiding_strat]
        
        x_var = 'tactic'
        hue_var = 'swarm_size' if group_by == 'n_hiders' else 'n_hiders'
        col_var = group_by
        
        # Create grouped bar plot
        g = sns.barplot(data=subset, x=x_var, y=f'{metric}_mean', 
                       hue=hue_var, errorbar=None, ax=ax, dodge=True)
        
        # Add error bars manually
        x_cats = sorted(subset[x_var].unique())
        hue_cats = sorted(subset[hue_var].unique())
        num_hue = len(hue_cats)
        bar_width = 0.8 / num_hue
        
        for xi, x_val in enumerate(x_cats):
            for hi, hue_val in enumerate(hue_cats):
                sub = subset[(subset[x_var] == x_val) & (subset[hue_var] == hue_val)]
                if sub.empty:
                    continue
                y = sub[f"{metric}_mean"].values[0]
                hw = sub[f"{metric}_hw"].values[0]
                x = xi - 0.4 + bar_width/2 + hi*bar_width
                ax.errorbar(x, y, yerr=hw, fmt="none", c="black", capsize=3, lw=1)
        
        ax.set_title(f"Hiding: {hiding_strat}")
        ax.set_xlabel("Tactic")
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
    
    axes[0].set_ylabel(metric.replace('_', ' ').title())
    axes[-1].legend(title=hue_var.replace('_', ' ').title(), 
                   bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.suptitle(f"{metric.replace('_', ' ').title()} by Tactic and {hue_var.replace('_', ' ').title()}", 
                fontsize=14, y=1.00)
    plt.tight_layout()
    plt.show()

# Plot 4: Multi-metric comparison grid
def plot_multi_metric_comparison(data, metrics=['find_steps', 'area_covered', 
                                                'hider_frac_found', 'taken_down']):
    """4-panel plot showing multiple metrics for quick comparison"""
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    axes = axes.flatten()
    
    for ax, metric in zip(axes, metrics):
        # Plot for a specific configuration (e.g., swarm_size=5, greedy hiding)
        subset = data[(data['swarm_size'] == 5) & (data['hiding_strategy'] == 'greedy')]
        
        for tactic in sorted(subset['tactic'].unique()):
            tactic_data = subset[subset['tactic'] == tactic].sort_values('n_hiders')
            
            ax.plot(tactic_data['n_hiders'], tactic_data[f'{metric}_mean'], 
                   marker='o', label=tactic, linewidth=2)
            ax.fill_between(tactic_data['n_hiders'], 
                           tactic_data[f'{metric}_ci_low'], 
                           tactic_data[f'{metric}_ci_up'], alpha=0.2)
        
        ax.set_title(metric.replace('_', ' ').title())
        ax.set_xlabel("Number of Hiders")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    
    plt.suptitle("Multi-Metric Comparison (Swarm=5, Greedy Hiding)", fontsize=16)
    plt.tight_layout()
    plt.show()

# Plot 5: Performance summary across all tactics
def plot_performance_summary(data, metric='hider_frac_found'):
    """Box plot showing distribution of metric across all parameter combinations"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    hiding_strategies = sorted(data['hiding_strategy'].unique())
    
    for ax, hiding_strat in zip(axes, hiding_strategies):
        subset = data[data['hiding_strategy'] == hiding_strat]
        
        sns.boxplot(data=subset, x='tactic', y=f'{metric}_mean', 
                   hue='swarm_size', ax=ax)
        ax.set_title(f"Hiding: {hiding_strat}")
        ax.set_xlabel("Tactic")
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle(f"{metric.replace('_', ' ').title()} Distribution by Tactic", fontsize=14)
    plt.tight_layout()
    plt.show()

# Main execution
if __name__ == "__main__":
    # Load data
    print("Loading simulation results...")
    all_data = load_all_results()
    print(f"Loaded {len(all_data)} simulation results")
    print(f"\nData shape: {all_data.shape}")
    print(f"Tactics: {sorted(all_data['tactic'].unique())}")
    print(f"Hiding strategies: {sorted(all_data['hiding_strategy'].unique())}")
    print(f"Swarm sizes: {sorted(all_data['swarm_size'].unique())}")
    print(f"N hiders: {sorted(all_data['n_hiders'].unique())}")
    
    # Generate all plots
    print("\n=== Generating Plots ===\n")
    
    # Key metrics to analyze
    key_metrics = ['find_steps', 'hider_frac_found', 'area_covered', 'taken_down']
    
    # 1. Trend plots
    print("1. Creating trend plots...")
    for metric in key_metrics:
        plot_trends_by_n_hiders(all_data, metric=metric)
    
    # 2. Heatmaps
    print("2. Creating heatmaps...")
    for metric in key_metrics:
        plot_heatmap_by_tactic(all_data, metric=metric)
    
    # 3. Grouped bar charts
    print("3. Creating grouped bar charts...")
    for metric in key_metrics:
        plot_grouped_bars_with_errors(all_data, metric=metric, group_by='n_hiders')
    
    # 4. Multi-metric comparison
    print("4. Creating multi-metric comparison...")
    plot_multi_metric_comparison(all_data, metrics=key_metrics)
    
    # 5. Performance summary
    print("5. Creating performance summary...")
    for metric in ['hider_frac_found', 'find_steps']:
        plot_performance_summary(all_data, metric=metric)
    
    print("\nAll plots generated successfully!")
