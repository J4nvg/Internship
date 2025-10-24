import os
import re
import pandas as pd
import numpy as np
from scipy.stats import binomtest
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px

# --- 1. CONFIGURATION ---

# Directory to scan for CSV files
DATA_DIR = '.' 

# Regex to parse filenames
# T-{TACTIC}-W-{GRIDWIDTH}-HS-{HidingStrategy}-D-{Swarmsize}-C-{HidingCandidates}-H-{NumberOfHiders}-RUNS-{NumberOfRuns}.csv
FILENAME_PATTERN = re.compile(
    r"T-(.+)"                  # Group 1: TACTIC
    r"-W-(\d+)"                # Group 2: GRIDWIDTH
    r"-HS-(.+)"                # Group 3: HidingStrategy
    r"-D-(\d+)"                # Group 4: Swarmsize
    r"-C-(\d+)"                # Group 5: HidingCandidates
    r"-H-(\d+)"                # Group 6: NumberOfHiders
    r"-RUNS-(\d+)\.csv"        # Group 7: NumberOfRuns
)

# --- 2. HELPER FUNCTIONS ---

def hex_to_rgb_str(hex_color):
    """Converts a hex color string (#FFFFFF) to an RGB string (255,255,255)."""
    hex_color = hex_color.lstrip('#')
    return ','.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

def scan_simulation_files(data_dir):
    """
    Scans the data directory, parses filenames, and returns a DataFrame
    of all found simulations and their parameters.
    """
    print("Scanning for simulation log files...")
    found_files = []
    for filename in os.listdir(data_dir):
        if not filename.endswith('.csv'):
            continue
        
        match = FILENAME_PATTERN.match(filename)
        if not match:
            continue
        
        try:
            found_files.append({
                'tactic': match.group(1),
                'width': int(match.group(2)),
                'hs': match.group(3),
                'swarm': int(match.group(4)),
                'candidates': int(match.group(5)),
                'hiders': int(match.group(6)),
                'runs': int(match.group(7)),
                'filename': filename
            })
        except ValueError:
            print(f"Warning: Could not parse parameters from {filename}")
    
    if not found_files:
        print("--- FATAL ERROR ---")
        print(f"No valid log files found in directory: {os.path.abspath(data_dir)}")
        print("Please check DATA_DIR and your file naming convention.")
        return pd.DataFrame()

    print(f"Found {len(found_files)} log files.")
    return pd.DataFrame(found_files)

def create_dropdown_options(values):
    """Creates a list of dictionaries for Dash dropdown options."""
    return [{'label': str(val), 'value': val} for val in sorted(pd.Series(values).unique())]

# --- 3. PRE-SCAN FILES AND PREPARE APP DATA ---

# Scan directory *once* on startup
ALL_FILES_DF = scan_simulation_files(DATA_DIR)

if ALL_FILES_DF.empty:
    exit()

# Get unique values for each parameter to populate dropdowns
WIDTH_OPTIONS = create_dropdown_options(ALL_FILES_DF['width'])
HS_OPTIONS = create_dropdown_options(ALL_FILES_DF['hs'])
SWARM_OPTIONS = create_dropdown_options(ALL_FILES_DF['swarm'])
CANDIDATES_OPTIONS = create_dropdown_options(ALL_FILES_DF['candidates'])
HIDERS_OPTIONS = create_dropdown_options(ALL_FILES_DF['hiders'])
RUNS_OPTIONS = create_dropdown_options(ALL_FILES_DF['runs'])

# Get color cycle for plotting
PLOT_COLORS = px.colors.qualitative.Plotly

# --- 4. DASH APP LAYOUT ---

app = dash.Dash(__name__, title="Swarm Simulation Analyzer")

# Define styles for layout
STYLES = {
    'container': {
        'fontFamily': '"Inter", Arial, sans-serif',
        'display': 'flex',
        'flexDirection': 'row',
        'height': '100vh',
        'width': '100vw',
        'margin': 0,
        'padding': 0
    },
    'controls': {
        'width': '380px',
        'padding': '20px',
        'backgroundColor': '#f9f9f9',
        'overflowY': 'auto',
        'borderRight': '1px solid #ddd'
    },
    'graph': {
        'flex': 1,
        'padding': '20px',
        'display': 'flex',
        'flexDirection': 'column',
        'height': '100%'
    },
    'control_item': {
        'marginBottom': '15px'
    },
    'label': {
        'fontWeight': 'bold',
        'marginBottom': '5px',
        'display': 'block'
    }
}

app.layout = html.Div(style=STYLES['container'], children=[
    
    # --- Control Panel (Left Side) ---
    html.Div(style=STYLES['controls'], children=[
        html.H2("Simulation Analyzer", style={'textAlign': 'center', 'marginTop': 0}),
        html.P("Select parameters to plot:", style={'textAlign': 'center'}),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("Grid Width (W):", style=STYLES['label']),
            dcc.Dropdown(id='dropdown-width', options=WIDTH_OPTIONS, value=WIDTH_OPTIONS[0]['value'] if WIDTH_OPTIONS else None)
        ]),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("Hiding Strategy (HS):", style=STYLES['label']),
            dcc.Dropdown(id='dropdown-hs', options=HS_OPTIONS, value=HS_OPTIONS[0]['value'] if HS_OPTIONS else None)
        ]),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("Swarm Size (D):", style=STYLES['label']),
            dcc.Dropdown(id='dropdown-swarm', options=SWARM_OPTIONS, value=SWARM_OPTIONS[0]['value'] if SWARM_OPTIONS else None)
        ]),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("Hiding Candidates (C):", style=STYLES['label']),
            dcc.Dropdown(id='dropdown-candidates', options=CANDIDATES_OPTIONS, value=CANDIDATES_OPTIONS[0]['value'] if CANDIDATES_OPTIONS else None)
        ]),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("Number of Hiders (H):", style=STYLES['label']),
            dcc.Dropdown(id='dropdown-hiders', options=HIDERS_OPTIONS, value=HIDERS_OPTIONS[0]['value'] if HIDERS_OPTIONS else None)
        ]),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("Number of Runs (RUNS):", style=STYLES['label']),
            dcc.Dropdown(id='dropdown-runs', options=RUNS_OPTIONS, value=RUNS_OPTIONS[0]['value'] if RUNS_OPTIONS else None)
        ]),
        
        html.Hr(),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("T Max (Stepslimit):", style=STYLES['label']),
            dcc.Input(id='input-t-max', type='number', value=4000, step=100, style={'width': '100%', 'boxSizing': 'border-box'})
        ]),
        
        html.Div(style=STYLES['control_item'], children=[
            html.Label("T Step (Plot Smoothness):", style=STYLES['label']),
            dcc.Input(id='input-t-step', type='number', value=20, min=1, step=1, style={'width': '100%', 'boxSizing': 'border-box'})
        ]),
    ]),
    
    # --- Graph Area (Right Side) ---
    html.Div(style=STYLES['graph'], children=[
        dcc.Graph(id='prob-plot', style={'flex': 1})
    ])
])

# --- 5. DASH CALLBACK (The Interactive Logic) ---

@app.callback(
    Output('prob-plot', 'figure'),
    [
        Input('dropdown-width', 'value'),
        Input('dropdown-hs', 'value'),
        Input('dropdown-swarm', 'value'),
        Input('dropdown-candidates', 'value'),
        Input('dropdown-hiders', 'value'),
        Input('dropdown-runs', 'value'),
        Input('input-t-max', 'value'),
        Input('input-t-step', 'value')
    ]
)
def update_graph(selected_width, selected_hs, selected_swarm, 
                 selected_candidates, selected_hiders, selected_runs,
                 t_max, t_step):

    # --- 5a. Handle Empty Inputs ---
    if not all([selected_width, selected_hs, selected_swarm, selected_candidates, 
                selected_hiders, selected_runs, t_max, t_step]):
        # Prevent errors on startup or if a dropdown is cleared
        return go.Figure().update_layout(
            title="Please select all parameters to load data",
            template="plotly_white"
        )
    
    # --- 5b. Filter Files ---
    # Find all files that match the user's selected parameters
    matching_files = ALL_FILES_DF[
        (ALL_FILES_DF['width'] == selected_width) &
        (ALL_FILES_DF['hs'] == selected_hs) &
        (ALL_FILES_DF['swarm'] == selected_swarm) &
        (ALL_FILES_DF['candidates'] == selected_candidates) &
        (ALL_FILES_DF['hiders'] == selected_hiders) &
        (ALL_FILES_DF['runs'] == selected_runs)
    ]

    fig = go.Figure()
    
    if matching_files.empty:
        return fig.update_layout(
            title=f"No data files found for the selected combination.",
            template="plotly_white"
        )

    # --- 5c. Calculate Data for Plotting ---
    T_values = np.arange(0, t_max + t_step, t_step)
    tactic_names = matching_files['tactic'].unique()

    for i, tactic in enumerate(tactic_names):
        
        file_row = matching_files[matching_files['tactic'] == tactic].iloc[0]
        filename = file_row['filename']
        n_total_runs = file_row['runs'] # Use the 'runs' from the filename
        
        try:
            df = pd.read_csv(os.path.join(DATA_DIR, filename), header=0, sep=r'\s+')
            if 'all_hiders_found' not in df.columns:
                 print(f"Skipping {filename}: 'all_hiders_found' column missing.")
                 continue

            # This is the core logic from your script
            successful_runs = df[df['all_hiders_found'] == 1]
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        probabilities = []
        ci_low = []
        ci_high = []

        for T in T_values:
            k_success_within_T = (successful_runs['steps'] <= T).sum()
            
            # Use n_total_runs from the filename, as in your script
            result = binomtest(k=k_success_within_T, n=n_total_runs)
            
            probabilities.append(result.statistic)
            ci = result.proportion_ci()
            ci_low.append(ci.low)
            ci_high.append(ci.high)

        # --- 5d. Add Traces to Plotly Figure ---
        color_hex = PLOT_COLORS[i % len(PLOT_COLORS)]
        color_rgb_str = hex_to_rgb_str(color_hex)
        
        # Create a closed loop for the confidence interval
        x_ci = np.concatenate([T_values, T_values[::-1]])
        y_ci = np.concatenate([ci_high, np.array(ci_low)[::-1]])

        # Add the filled CI area (transparent)
        fig.add_trace(go.Scatter(
            x=x_ci,
            y=y_ci,
            fill='toself',
            fillcolor=f'rgba({color_rgb_str}, 0.2)',
            line=dict(color='rgba(255,255,255,0)'), # No border
            hoverinfo="none",
            showlegend=False,
            name=f'{tactic} CI'
        ))
        
        # Add the main probability line
        fig.add_trace(go.Scatter(
            x=T_values,
            y=probabilities,
            name=tactic,
            mode='lines',
            line=dict(color=color_hex, width=2)
        ))

    # --- 5e. Format and Return Figure ---
    title = (
        f'Probability of All Hiders Found vs. Stepslimit (T)<br>'
        f'Swarm={selected_swarm}, Hiders={selected_hiders}, Grid={selected_width}, '
        f'HS={selected_hs}, Candidates={selected_candidates}'
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='Stepslimit T',
        yaxis_title='P(All Found | steps ≤ T)',
        yaxis_range=[0, 1.05],
        xaxis_range=[0, t_max],
        template="plotly_white",
        hovermode="x unified",
        legend_title_text='Tactics',
        legend=dict(
            yanchor="bottom",
            y=0.01,
            xanchor="right",
            x=0.99
        )
    )

    return fig

# --- 6. RUN THE APP ---
if __name__ == '__main__':
    if ALL_FILES_DF.empty:
        print("\nApplication will not start as no data files were found.")
    else:
        print("Dash app starting... Open http://127.0.0.1:8050/ in your browser.")
        app.run(debug=True, port=8050)
