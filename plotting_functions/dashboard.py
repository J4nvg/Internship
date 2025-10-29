import os
import pandas as pd
import numpy as np
from scipy.stats import binomtest
import re
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Configuration
tactic_abbr_full = {
    "ttbp": "together_traverse_best_permutation",
    "dor": "divide_over_risks",
    "rndm": "random_walk",
    "hs": "horizontal_scan_traversal",
    "phs": "partitioned_horizontal_scan_traversal",
    "sp": "spiral_traversal_swarm",
    "lb": "lidbetter",
    "toq": "traverse_ordered_qa",
    "tpq": "traverse_p_qa",
    "dd": "discounted_distance",
}

SUMMARY_FILENAME = '../data/dataset/sim_results_dataset.csv'
SIMLOGS = "../data/sim_logs/"

FIXED_HIDING_CANDIDATES = 5
FIXED_GRID_WIDTH = 20
FIXED_NUMBER_OF_RUNS = 100000

# Load data
df_all = pd.read_csv(SUMMARY_FILENAME)

# Get available options
available_hide_strategies = sorted(df_all['hide_strategy'].unique())
available_n_hiders = sorted(df_all['n_hiders'].unique())
available_swarm_sizes = sorted(df_all['swarm_size'].unique())

# Color mapping
all_tactic_names = sorted(tactic_abbr_full.values())
colors = px.colors.qualitative.Plotly
tactic_colors = {tactic: colors[i % len(colors)] for i, tactic in enumerate(all_tactic_names)}

# Initialize Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Hide and Seek Simulation Dashboard", style={'textAlign': 'center'}),

    # Controls Section
    html.Div([
        html.Div([
            html.Label("Hiding Strategy:"),
            dcc.Dropdown(
                id='hide-strategy-dropdown',
                options=[{'label': hs, 'value': hs} for hs in available_hide_strategies],
                value=available_hide_strategies[0] if available_hide_strategies else None,
                style={'width': '200px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '20px'}),

        html.Div([
            html.Label("Number of Hiders:"),
            dcc.Dropdown(
                id='n-hiders-dropdown',
                options=[{'label': str(n), 'value': n} for n in available_n_hiders],
                value=available_n_hiders[0] if available_n_hiders else None,
                style={'width': '200px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
    ], style={'padding': '20px', 'backgroundColor': '#f0f0f0'}),

    # Plot 1: P(All Found) vs Swarm Size
    html.Div([
        html.H2("Plot 1: P(All Found) vs Swarm Size"),
        dcc.Graph(id='plot1-swarm-size')
    ], style={'padding': '20px'}),

    # Controls for Plot 2
    html.Div([
        html.H2("Plot 2: P(All Found) vs Step Limit"),
        html.Label("Swarm Size:"),
        dcc.Dropdown(
            id='swarm-size-dropdown',
            options=[{'label': str(s), 'value': s} for s in available_swarm_sizes],
            value=available_swarm_sizes[0] if available_swarm_sizes else None,
            style={'width': '200px'}
        ),
    ], style={'padding': '20px', 'backgroundColor': '#f0f0f0'}),

    # Plot 2: P(All Found) vs Step Limit
    html.Div([
        dcc.Graph(id='plot2-step-limit'),
        html.Div(id='plot2-status', style={'padding': '10px', 'fontStyle': 'italic'})
    ], style={'padding': '20px'}),
])


@app.callback(
    Output('plot1-swarm-size', 'figure'),
    [Input('hide-strategy-dropdown', 'value'),
     Input('n-hiders-dropdown', 'value')]
)
def update_plot1(hide_strategy, n_hiders):
    if hide_strategy is None or n_hiders is None:
        return go.Figure()

    # Filter data
    df_filtered = df_all[
        (df_all['hide_strategy'] == hide_strategy) &
        (df_all['n_hiders'] == n_hiders) &
        (df_all['n_hider_candidates'] == FIXED_HIDING_CANDIDATES) &
        (df_all['grid_width'] == FIXED_GRID_WIDTH) &
        (df_all['runs'] == FIXED_NUMBER_OF_RUNS)
        ]

    if df_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for selected parameters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig

    # Prepare results
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

    # Sort by final P value
    sorted_results = sorted(
        results.items(),
        key=lambda item: item[1]['P'][-1] if len(item[1]['P']) > 0 else -1,
        reverse=True
    )

    # Create figure
    fig = go.Figure()

    for tactic_name, data in sorted_results:
        if len(data['swarm_sizes']) == 0:
            continue

        color = tactic_colors.get(tactic_name, '#000000')

        # Add confidence interval
        fig.add_trace(go.Scatter(
            x=np.concatenate([data['swarm_sizes'], data['swarm_sizes'][::-1]]),
            y=np.concatenate([data['high'], data['low'][::-1]]),
            fill='toself',
            fillcolor=color,
            opacity=0.15,
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add main line
        fig.add_trace(go.Scatter(
            x=data['swarm_sizes'],
            y=data['P'],
            mode='lines+markers',
            name=tactic_name,
            line=dict(color=color, width=2),
            marker=dict(size=8)
        ))

    fig.update_layout(
        title=f'Probability of All Hiders Found vs. Swarm Size<br>Hiders={n_hiders}, HS={hide_strategy}, Grid={FIXED_GRID_WIDTH}x{FIXED_GRID_WIDTH}',
        xaxis_title='Swarm Size',
        yaxis_title='P(All Found)',
        yaxis=dict(range=[0, 1]),
        hovermode='x unified',
        legend=dict(title='Tactics', x=0, y=1),
        template='plotly_white'
    )

    return fig


@app.callback(
    [Output('plot2-step-limit', 'figure'),
     Output('plot2-status', 'children')],
    [Input('hide-strategy-dropdown', 'value'),
     Input('n-hiders-dropdown', 'value'),
     Input('swarm-size-dropdown', 'value')]
)
def update_plot2(hide_strategy, n_hiders, swarm_size):
    if hide_strategy is None or n_hiders is None or swarm_size is None:
        return go.Figure(), "Please select all parameters"

    # File pattern
    filename_pattern = re.compile(
        r"T-(.+)"
        r"-W-(\d+)"
        r"-HS-(.+)"
        r"-D-(\d+)"
        r"-C-(\d+)"
        r"-H-(\d+)"
        r"-RUNS-(\d+)\.csv"
    )

    T_MIN = 0
    T_MAX = 1000
    T_STEP = 10
    T_values = np.arange(T_MIN, T_MAX + T_STEP, T_STEP)

    results = {}
    tactic_files_found = []

    # Search for matching files
    if not os.path.exists(SIMLOGS):
        return go.Figure(), f"Directory not found: {SIMLOGS}"

    for filename in os.listdir(SIMLOGS):
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
                hs == hide_strategy and
                candidates == FIXED_HIDING_CANDIDATES and
                hiders == n_hiders and
                width == FIXED_GRID_WIDTH and
                runs == FIXED_NUMBER_OF_RUNS):

            tactic_files_found.append(filename)

            df = pd.read_csv(os.path.join(SIMLOGS, filename), header=0, sep=r'\s+')
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
        fig = go.Figure()
        fig.add_annotation(
            text=f"No simulation logs found for:<br>HS={hide_strategy}, Hiders={n_hiders}, Swarm={swarm_size}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14)
        )
        status = f"Found 0 matching files"
        return fig, status

    # Sort by final P value
    sorted_results = sorted(
        results.items(),
        key=lambda item: item[1]['P'][-1],
        reverse=True
    )

    # Create figure
    fig = go.Figure()

    for tactic_name, data in sorted_results:
        color = tactic_colors.get(tactic_name, '#000000')

        # Add confidence interval
        fig.add_trace(go.Scatter(
            x=np.concatenate([data['T'], data['T'][::-1]]),
            y=np.concatenate([data['high'], data['low'][::-1]]),
            fill='toself',
            fillcolor=color,
            opacity=0.2,
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add main line
        fig.add_trace(go.Scatter(
            x=data['T'],
            y=data['P'],
            mode='lines',
            name=tactic_name,
            line=dict(color=color, width=2)
        ))

    fig.update_layout(
        title=f'Probability of All Hiders Found vs. Step Limit (T)<br>Swarm Size={swarm_size}, Hiders={n_hiders}, Grid={FIXED_GRID_WIDTH}x{FIXED_GRID_WIDTH}, HS={hide_strategy}',
        xaxis_title='Step Limit T',
        yaxis_title='P(All Found | steps ≤ T)',
        yaxis=dict(range=[0, 1]),
        xaxis=dict(range=[T_MIN, T_MAX]),
        hovermode='x unified',
        legend=dict(title='Tactics', x=1, y=0, xanchor='right', yanchor='bottom'),
        template='plotly_white'
    )

    status = f"Found {len(tactic_files_found)} matching simulation log files"
    return fig, status


if __name__ == '__main__':
    app.run(debug=True, port=8050)