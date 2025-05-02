# /home/wmfs0449/reddit_dashboard/src/dashboard.py
import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
import os
import glob
from dash.dependencies import Input, Output
from datetime import datetime # Needed for filename parsing

DATA_DIR = "/app/data"

def find_latest_csv(directory):
    """Finds the most recent CSV file in the specified directory based on filename date."""
    list_of_files = glob.glob(os.path.join(directory, 'reddit_trends_*.csv'))
    if not list_of_files:
        print(f"No CSV files found matching pattern in {directory}")
        return None

    # Use filename sorting for reliability
    files_with_dates = {}
    for f in list_of_files:
        try:
            # Extract date string assuming format reddit_trends_YYYYMMDD.csv
            date_str = os.path.basename(f).replace('reddit_trends_', '').replace('.csv', '')
            # Validate date format
            file_date = datetime.strptime(date_str, '%Y%m%d')
            files_with_dates[f] = file_date
        except ValueError:
            print(f"Skipping file with unexpected name format: {f}")
            continue # Skip files not matching the pattern

    if not files_with_dates:
        print(f"No valid dated CSV files found in {directory}")
        return None

    # Find the file path corresponding to the latest date
    latest_file = max(files_with_dates, key=files_with_dates.get)
    print(f"Found latest CSV: {latest_file}")
    return latest_file


def load_data():
    """Loads data from the latest CSV file."""
    latest_csv = find_latest_csv(DATA_DIR)
    if latest_csv and os.path.exists(latest_csv):
        try:
            df = pd.read_csv(latest_csv)
            print(f"Successfully loaded data from {latest_csv}")
            # Basic data cleaning/preparation
            df['created_utc'] = pd.to_datetime(df['created_utc'])
            df['author'] = df['author'].fillna('N/A')
            df['flair'] = df['flair'].fillna('None')
            # Ensure numeric columns are numeric, coercing errors
            numeric_cols = ['score', 'num_comments']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=numeric_cols) # Drop rows where score/comments couldn't be parsed
            df['score'] = df['score'].astype(int)
            df['num_comments'] = df['num_comments'].astype(int)

            return df, latest_csv
        except Exception as e:
            print(f"Error loading or processing data from {latest_csv}: {e}")
            return pd.DataFrame(), None # Return empty DataFrame on error
    else:
        print(f"No CSV data file found or accessible in {DATA_DIR}")
        return pd.DataFrame(), None # Return empty DataFrame if no file found

# Initialize Dash app within the create_dashboard function
def create_dashboard(flask_server):
    """Creates and configures the Dash application."""
    # Use external stylesheets for better appearance
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__,
                    server=flask_server,
                    url_base_pathname='/', # Serve Dash app at root
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True) # Suppress errors until layout is fully generated

    # Load initial data to setup layout structure
    df_initial, data_file_initial = load_data()
    initial_columns = [{"name": i, "id": i} for i in df_initial.columns] if not df_initial.empty else []
    initial_data = df_initial.to_dict('records') if not df_initial.empty else []
    data_file_basename = os.path.basename(data_file_initial) if data_file_initial else 'No data found'

    # Define App Layout
    app.layout = html.Div(children=[
        html.H1(children='Reddit Trend Dashboard'),

        html.Div(id='data-info', children=f'Visualizing trends from r/popular. Data from: {data_file_basename}'),

        html.Hr(),

        # Section 1: Top Posts by Score
        html.H2("Top Posts by Score"),
        dcc.Graph(id='top-posts-score-graph'),

        # Section 2: Subreddit Frequency
        html.H2("Most Frequent Subreddits in r/popular Feed"),
        dcc.Graph(id='subreddit-frequency-graph'),

        # Section 3: Data Table
        html.H2("Raw Data"),
        dash_table.DataTable(
            id='data-table',
            columns=initial_columns,
            data=initial_data,
            page_size=10, # Show 10 rows per page
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            selected_rows=[],
            page_action="native",
            style_table={'overflowX': 'auto'},
             style_cell={
                'height': 'auto',
                'minWidth': '100px', 'width': '150px', 'maxWidth': '300px',
                'whiteSpace': 'normal'
            }
        ),

        # Hidden div to trigger callback on load
        html.Div(id='trigger-load', children=0, style={'display': 'none'}),

    ])

    # Define Callbacks to update graphs and table
    @app.callback(
        [Output('top-posts-score-graph', 'figure'),
         Output('subreddit-frequency-graph', 'figure'),
         Output('data-table', 'columns'),
         Output('data-table', 'data'),
         Output('data-info', 'children')],
        [Input('trigger-load', 'children')] # Trigger on initial load
    )
    def update_dashboard(n):
        print("Update dashboard callback triggered.")
        df_callback, data_file_callback = load_data()
        data_file_basename_callback = os.path.basename(data_file_callback) if data_file_callback else 'No data found'
        info_text = f'Visualizing trends from r/popular. Data from: {data_file_basename_callback}'

        if df_callback.empty:
            print("No data loaded, returning empty components.")
            # Return empty figures/data if no file or error
            return {}, {}, [], [], info_text

        print(f"Data loaded successfully for callback. Shape: {df_callback.shape}")

        # Graph 1: Top Posts by Score (Top 20)
        try:
            top_posts = df_callback.nlargest(20, 'score')
            fig_score = px.bar(top_posts,
                               x='title', y='score',
                               title="Top 20 Posts by Score",
                               hover_data=['subreddit', 'num_comments', 'author', 'url'],
                               labels={'title': 'Post Title'})
            fig_score.update_layout(xaxis_title=None, yaxis_title="Score", xaxis_tickangle=-45) # Remove x-axis title, rotate labels
            print("Score graph generated.")
        except Exception as e:
            print(f"Error generating score graph: {e}")
            fig_score = {} # Empty figure on error

        # Graph 2: Subreddit Frequency (Top 20)
        try:
            # Use value_counts().nlargest().reset_index() to get counts and subreddit names
            subreddit_counts = df_callback['subreddit'].value_counts().nlargest(20).reset_index()
            # Check column names after reset_index (might be 'index', 'subreddit' or 'subreddit', 'count')
            # Assuming pandas >= 1.1.0, it should be 'subreddit', 'count'
            if list(subreddit_counts.columns) == ['index', 0]: # Older pandas compatibility
                 subreddit_counts.columns = ['subreddit', 'count']
            elif 'count' not in subreddit_counts.columns and len(subreddit_counts.columns) == 2: # Handle cases like ('subreddit', '0')
                 subreddit_counts.columns = ['subreddit', 'count']

            fig_subreddit = px.bar(subreddit_counts,
                                   x='subreddit', y='count',
                                   title="Top 20 Most Frequent Subreddits")
            fig_subreddit.update_layout(xaxis_title="Subreddit", yaxis_title="Number of Posts")
            print("Subreddit graph generated.")
        except Exception as e:
            print(f"Error generating subreddit graph: {e}")
            fig_subreddit = {} # Empty figure on error


        # Table Data
        try:
            table_columns = [{"name": i, "id": i} for i in df_callback.columns]
            table_data = df_callback.to_dict('records')
            print("Table data prepared.")
        except Exception as e:
            print(f"Error preparing table data: {e}")
            table_columns = []
            table_data = []

        return fig_score, fig_subreddit, table_columns, table_data, info_text

    return app # Return the configured Dash app instance

