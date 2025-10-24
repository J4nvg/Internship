import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output


try:
    df = pd.read_csv("../data/sim_results/combined_dataset.csv")
except FileNotFoundError:
    print("Error: 'combined_dataset.csv' not found.")
    print("Please make sure the script is in the same directory as the CSV file or update the path.")
    exit()

# --- Configuration ---

# Define the metrics available for plotting and their corresponding error columns
# Using 'hider_frac_found_mean' for 'found' as it has a half_width
METRICS_MAP = {
    'steps_mean': 'steps_half_width',
    'taken_down_mean': 'taken_down_half_width',
    'area_covered_mean': 'area_covered_half_width',
    'mean_distance_travelled_mean': 'mean_distance_travelled_half_width',
    'hider_frac_found_mean': 'hider_frac_found_half_width'
}
# Create a user-friendly mapping for dropdown labels
METRIC_LABELS = {
    'steps_mean': 'Steps (Mean)',
    'taken_down_mean': 'Drones Taken Down (Mean)',
    'area_covered_mean': 'Area Covered (Mean %)',
    'mean_distance_travelled_mean': 'Mean Distance Travelled (Mean)',
    'hider_frac_found_mean': 'Hiders Found (Mean Fraction)'
}

# Define the columns available for grouping
GROUPING_COLS = ['tactic', 'hide_strategy', 'n_hiders', 'swarm_size']

# --- Tactic Abbreviations ---
# Map full tactic names to abbreviations for cleaner plot labels
tactic_abbr_full = {
    "ttbp": "together_traverse_best_permutation",
    "dor": "divide_over_risks",
    "rndm": "random_walk",
    "hs": "horizontal_scan_traversal",
    "phs": "partitioned_horizontal_scan_traversal",
    # "vs":"vertical_scan_traversal",
    "sp": "spiral_traversal_swarm"
}
# Create a reverse map (full name -> abbreviation)
tactic_full_to_abbr = {v: k for k, v in tactic_abbr_full.items()}

if 'tactic' in df.columns:
    # Apply the map. Use fillna to keep any original tactic names that aren't in the map.
    df['tactic'] = df['tactic'].map(tactic_full_to_abbr).fillna(df['tactic'])
# --- End Tactic Abbreviations ---


# Convert numeric grouping columns to string type to treat them as categorical
# This ensures they are plotted as discrete groups, not a continuous axis
for col in ['n_hiders', 'swarm_size']:
    if col in df.columns:
        df[col] = df[col].astype(str)

# --- Initialize Dash App ---
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.title = "Simulation Metrics Dashboard"

# --- App Layout ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1(
        children='Interactive Simulation Metrics Dashboard',
        style={'textAlign': 'center', 'color': '#333'}
    ),

    html.P(
        "Use the dropdowns below to select the metric and configure the plot axes and groupings.",
        style={'textAlign': 'center', 'color': '#555', 'marginBottom': '20px'}
    ),

    # --- Control Panel (Horizontal Row) ---
    html.Div(className='row',
             style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'borderRadius': '8px', 'marginBottom': '30px'},
             children=[

                 html.Div(className='two columns', style={'paddingRight': '10px'}, children=[
                     html.Label('Select Metric (Y-axis):', style={'fontWeight': 'bold'}),
                     dcc.Dropdown(
                         id='y-metric-dropdown',
                         options=[{'label': label, 'value': value} for value, label in METRIC_LABELS.items()],
                         # <-- Fixed: METRICS_LABELS -> METRIC_LABELS
                         value='hider_frac_found_mean'  # Default metric
                     ),
                 ]),

                 html.Div(className='two columns', style={'paddingRight': '10px'}, children=[
                     html.Label('Select X-axis:', style={'fontWeight': 'bold'}),
                     dcc.Dropdown(
                         id='x-axis-dropdown',
                         options=[{'label': col, 'value': col} for col in GROUPING_COLS],
                         value='swarm_size'  # Default x-axis
                     ),
                 ]),

                 html.Div(className='two columns', style={'paddingRight': '10px'}, children=[
                     html.Label('Select Grouping (Color):', style={'fontWeight': 'bold'}),
                     dcc.Dropdown(
                         id='color-dropdown',
                         options=[{'label': col, 'value': col} for col in GROUPING_COLS],
                         value='n_hiders'  # Default grouping
                     ),
                 ]),

                 html.Div(className='three columns', style={'paddingRight': '10px'}, children=[
                     html.Label('Select Facet Row:', style={'fontWeight': 'bold'}),
                     dcc.Dropdown(
                         id='facet-row-dropdown',
                         options=[{'label': 'None', 'value': 'None'}] + [{'label': col, 'value': col} for col in
                                                                         GROUPING_COLS],
                         value='tactic'  # Default facet row
                     ),
                 ]),

                 html.Div(className='three columns', children=[
                     html.Label('Select Facet Column:', style={'fontWeight': 'bold'}),
                     dcc.Dropdown(
                         id='facet-col-dropdown',
                         options=[{'label': 'None', 'value': 'None'}] + [{'label': col, 'value': col} for col in
                                                                         GROUPING_COLS],
                         value='hide_strategy'  # Default facet column
                     ),
                 ]),
             ]),

    # --- Plot Area (Full Width) ---
    html.Div(className='row', children=[
        html.Div(className='twelve columns', children=[
            dcc.Loading(
                id="loading-spinner",
                type="circle",
                children=dcc.Graph(id='metrics-plot', style={'height': '80vh'})  # Taller plot
            )
        ]),
    ]),
])


# --- Callback Function ---
@app.callback(
    Output('metrics-plot', 'figure'),
    [
        Input('y-metric-dropdown', 'value'),
        Input('x-axis-dropdown', 'value'),
        Input('color-dropdown', 'value'),
        Input('facet-row-dropdown', 'value'),
        Input('facet-col-dropdown', 'value')
    ]
)
def update_graph(y_metric, x_col, color_col, facet_row, facet_col):
    # Handle 'None' selections for facets
    facet_row_val = None if facet_row == 'None' else facet_row
    facet_col_val = None if facet_col == 'None' else facet_col

    # Get the corresponding error bar column
    error_col = METRICS_MAP[y_metric]

    # Get the user-friendly label for the metric
    y_label = METRIC_LABELS[y_metric]

    # Create the figure
    try:
        fig = px.bar(
            df,
            x=x_col,
            y=y_metric,
            color=color_col,
            facet_row=facet_row_val,
            facet_col=facet_col_val,
            error_y=error_col,  # Add error bars
            barmode='group',  # Ensure bars are grouped
            labels={y_metric: y_label, x_col: x_col.title()},  # Add labels
            height=700 if not facet_row_val else 800  # Make plot taller, especially for facets
        )

        # Update layout for better readability
        fig.update_layout(
            margin=dict(t=50, l=25, r=25, b=25),
            title=f"Metric Analysis: {y_label}",
            legend_title=color_col.title(),
        )
        # Sort x-axis if it's one of the numeric-like categories
        if x_col in ['n_hiders', 'swarm_size']:
            # Sort numerically by converting back to int, then to string
            sorted_categories = sorted(df[x_col].unique(), key=int)
            fig.update_xaxes(categoryorder='array', categoryarray=sorted_categories)

        # Make facet titles cleaner
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        # --- FIX for overlapping Y-axis labels ---
        # Hide Y-axis titles for all subplots except the bottom one (yaxis)
        # Plotly names them yaxis, yaxis2, yaxis3, ...
        # We keep the title on 'yaxis' and remove it from all others.
        for axis in fig.layout:
            if axis.startswith('yaxis') and axis != 'yaxis':
                fig.layout[axis].title.text = ""
        # --- End Fix ---

        return fig

    except Exception as e:
        print(f"Error plotting: {e}")
        # Return an empty figure on error
        return px.bar().update_layout(
            title=f"Error: Could not plot graph. Check console for details.",
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{'text': str(e), 'showarrow': False}]
        )


# --- Run the App ---
if __name__ == '__main__':
    print("Dash server starting...")

app.run(debug=True, port=8050)

