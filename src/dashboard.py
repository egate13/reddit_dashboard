# /home/wmfs0449/reddit_dashboard/src/dashboard.py
import dash
from dash import dcc, html, dash_table, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import glob
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
from supabase import create_client # Removed unused Client
import io
import re # For keyword searching

DATA_DIR = "/home/wmfs0449/reddit_dashboard/data"

# Supabase configuration
SUPABASE_URL = "https://mcvnrkoogobezgjcsivw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1jdm5ya29vZ29iZXpnamNzaXZ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzgzMjIyNCwiZXhwIjoyMDYzNDA4MjI0fQ.D-uJysR1NPx1gZNdHPiNdjgFlZ1lLTJB_dJ2exopD_E"
BUCKET_NAME = "redditdashboard"

# Couleurs pour les graphiques
COLORS = {
    'primary': '#FF4500',    # Orange Reddit
    'secondary': '#0079D3',  # Bleu Reddit
    'background': '#F8F9FA', # Un gris clair pour le fond général
    'card_background': '#FFFFFF', # Blanc pour les cartes/conteneurs de graphiques
    'text': '#1A1A1B',       # Couleur de texte principale
    'light_text': '#555555', # Texte plus clair pour les sous-titres ou infos
    'grid': '#EDEFF1',       # Couleur pour les grilles des graphiques
    'accent': '#FFD700'      # Une couleur d'accent (Or)
}

def get_all_csv_from_supabase():
    """Récupère tous les fichiers CSV du bucket Supabase"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.storage.from_(BUCKET_NAME).list()
        
        if not response:
            print(f"No files found in Supabase bucket '{BUCKET_NAME}'")
            return pd.DataFrame(), []
        
        csv_files = [file for file in response if file.get('name', '').startswith('reddit_trends_') and file.get('name', '').endswith('.csv')]
        
        if not csv_files:
            print(f"No CSV files found matching pattern in Supabase bucket")
            return pd.DataFrame(), []
            
        files_with_dates = {}
        for file in csv_files:
            try:
                filename = file.get('name')
                date_str = filename.replace('reddit_trends_', '').replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y%m%d')
                files_with_dates[filename] = file_date
            except ValueError:
                print(f"Skipping file with unexpected name format: {file.get('name')}")
                continue
        
        sorted_files = sorted(files_with_dates.items(), key=lambda x: x[1], reverse=True)
        
        all_data = []
        file_list = []
        for filename, file_date in sorted_files:
            try:
                file_data = supabase.storage.from_(BUCKET_NAME).download(filename)
                df_temp = pd.read_csv(io.BytesIO(file_data))
                df_temp['file_date'] = file_date # Keep as datetime for now
                all_data.append(df_temp)
                file_list.append({'name': filename, 'date': file_date.strftime('%Y-%m-%d')})
                print(f"Downloaded and processed: {filename}")
            except Exception as e:
                print(f"Error downloading or processing {filename}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame(), []
            
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # --- Centralized Data Cleaning ---
        combined_df['created_utc'] = pd.to_datetime(combined_df['created_utc'])
        combined_df['author'] = combined_df['author'].fillna('N/A')
        combined_df['flair'] = combined_df['flair'].fillna('None')
        # Ensure 'title' and 'selftext' are strings
        if 'title' in combined_df.columns:
            combined_df['title'] = combined_df['title'].fillna('').astype(str)
        if 'selftext' in combined_df.columns: # Assuming you might have selftext
             combined_df['selftext'] = combined_df['selftext'].fillna('').astype(str)
        else: # Add selftext if not present, for keyword search consistency
            combined_df['selftext'] = ''


        numeric_cols = ['score', 'num_comments']
        for col in numeric_cols:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
        combined_df = combined_df.dropna(subset=numeric_cols) # Drop rows where score/comments couldn't be parsed
        combined_df['score'] = combined_df['score'].astype(int)
        combined_df['num_comments'] = combined_df['num_comments'].astype(int)
        combined_df['file_date'] = pd.to_datetime(combined_df['file_date']).dt.strftime('%Y-%m-%d') # Now convert to string

        return combined_df, file_list
    
    except Exception as e:
        print(f"Error accessing Supabase storage (get_all_csv_from_supabase): {e}")
        return pd.DataFrame(), []

def find_latest_csv_from_supabase():
    """Finds the most recent CSV file in Supabase bucket based on filename date."""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.storage.from_(BUCKET_NAME).list()
        
        if not response:
            print(f"No files found in Supabase bucket '{BUCKET_NAME}'")
            return None, None
            
        csv_files = [file for file in response if file.get('name', '').startswith('reddit_trends_') and file.get('name', '').endswith('.csv')]
        
        if not csv_files:
            print(f"No CSV files found matching pattern in Supabase bucket")
            return None, None
            
        files_with_dates = {}
        for file in csv_files:
            try:
                filename = file.get('name')
                date_str = filename.replace('reddit_trends_', '').replace('.csv', '')
                file_date = datetime.strptime(date_str, '%Y%m%d')
                files_with_dates[filename] = file_date
            except ValueError:
                print(f"Skipping file with unexpected name format: {file.get('name')}")
                continue
        
        if not files_with_dates:
            print(f"No valid dated CSV files found in Supabase bucket")
            return None, None
            
        latest_filename = max(files_with_dates, key=files_with_dates.get)
        file_data = supabase.storage.from_(BUCKET_NAME).download(latest_filename)
        
        print(f"Found and downloaded latest CSV from Supabase: {latest_filename}")
        return file_data, latest_filename
    
    except Exception as e:
        print(f"Error accessing Supabase storage (find_latest_csv_from_supabase): {e}")
        return None, None

def find_latest_csv(directory):
    """Finds the most recent CSV file in the specified directory based on filename date."""
    list_of_files = glob.glob(os.path.join(directory, 'reddit_trends_*.csv'))
    if not list_of_files:
        print(f"No CSV files found matching pattern in {directory}")
        return None

    files_with_dates = {}
    for f in list_of_files:
        try:
            date_str = os.path.basename(f).replace('reddit_trends_', '').replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y%m%d')
            files_with_dates[f] = file_date
        except ValueError:
            print(f"Skipping file with unexpected name format: {f}")
            continue 

    if not files_with_dates:
        print(f"No valid dated CSV files found in {directory}")
        return None

    latest_file = max(files_with_dates, key=files_with_dates.get)
    print(f"Found latest CSV: {latest_file}")
    return latest_file

def _clean_dataframe(df, filename_for_date=None):
    """Helper function to clean a dataframe and add file_date if filename is provided."""
    df['created_utc'] = pd.to_datetime(df['created_utc'])
    df['author'] = df['author'].fillna('N/A')
    df['flair'] = df['flair'].fillna('None')
    if 'title' in df.columns:
        df['title'] = df['title'].fillna('').astype(str)
    if 'selftext' in df.columns: # Assuming you might have selftext
        df['selftext'] = df['selftext'].fillna('').astype(str)
    else: # Add selftext if not present, for keyword search consistency
        df['selftext'] = ''


    numeric_cols = ['score', 'num_comments']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=numeric_cols)
    df['score'] = df['score'].astype(int)
    df['num_comments'] = df['num_comments'].astype(int)
    
    if filename_for_date:
        try:
            date_str = os.path.basename(filename_for_date).replace('reddit_trends_', '').replace('.csv', '')
            file_date = datetime.strptime(date_str, '%Y%m%d')
            df['file_date'] = file_date.strftime('%Y-%m-%d')
        except ValueError:
            print(f"Warning: Could not parse date from filename {filename_for_date} for 'file_date' column.")
            df['file_date'] = datetime.now().strftime('%Y-%m-%d') # Fallback
    return df

def load_data(time_period='day'):
    """Loads data from CSV files based on time period, prioritizing Supabase."""
    if time_period in ['week', 'month', 'all']:
        combined_df, file_list = get_all_csv_from_supabase() # Already cleaned here
        if not combined_df.empty:
            print(f"Successfully loaded {len(file_list)} files from Supabase for {time_period} analysis.")
            
            combined_df['file_date_dt'] = pd.to_datetime(combined_df['file_date'])
            now = datetime.now()
            if time_period == 'week':
                cutoff_date = now - timedelta(days=7)
                combined_df = combined_df[combined_df['file_date_dt'] >= cutoff_date]
            elif time_period == 'month':
                month_ago = now - timedelta(days=30) # Defined month_ago
                combined_df = combined_df[combined_df['file_date_dt'] >= month_ago]
            
            if not combined_df.empty: # Check if df is empty after filtering
                combined_df = combined_df.drop(columns=['file_date_dt'])
            else: # if empty after filtering, return empty df with original columns
                empty_df_cols = list(combined_df.columns)
                empty_df_cols.remove('file_date_dt') # remove temporary column
                return pd.DataFrame(columns=empty_df_cols), f"Supabase: 0 files after time filter ({time_period} analysis)"

            return combined_df, f"Supabase: {len(file_list)} files ({time_period} analysis)"
        else:
            print(f"No data found in Supabase for {time_period} analysis, trying local files (not implemented for multi-file local).")

    file_data, latest_filename_supabase = find_latest_csv_from_supabase()
    
    if file_data:
        try:
            df = pd.read_csv(io.BytesIO(file_data))
            df = _clean_dataframe(df, latest_filename_supabase) # Cleaned here
            print(f"Successfully loaded data from Supabase: {latest_filename_supabase}")
            return df, f"Supabase: {latest_filename_supabase}"
        except Exception as e:
            print(f"Error processing data from Supabase: {e}. Trying local.")
    
    latest_csv_local = find_latest_csv(DATA_DIR)
    if latest_csv_local and os.path.exists(latest_csv_local):
        try:
            df = pd.read_csv(latest_csv_local)
            df = _clean_dataframe(df, latest_csv_local) # Cleaned here
            print(f"Successfully loaded data from local file: {latest_csv_local}")
            return df, f"Local: {os.path.basename(latest_csv_local)}"
        except Exception as e:
            print(f"Error loading or processing data from {latest_csv_local}: {e}")
            return pd.DataFrame(), "Error: Could not load local data."
            
    print(f"No CSV data file found or accessible (Supabase or local in {DATA_DIR}).")
    return pd.DataFrame(), "No data source found."


def create_dashboard(flask_server):
    """Creates and configures the Dash application."""
    external_stylesheets = [
        'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
        'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap'
    ]
    
    app = dash.Dash(__name__,
                    server=flask_server,
                    url_base_pathname='/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True,
                    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

    app.index_string = f'''
    <!DOCTYPE html>
    <html>
        <head>
            {{%metas%}}
            <title>Reddit Trends Dashboard</title>
            {{%favicon%}}
            {{%css%}}
            <style>
                body {{ font-family: 'Roboto', sans-serif; background-color: {COLORS['background']}; color: {COLORS['text']}; margin: 0; padding: 0; }}
                .dashboard-header {{ background-color: {COLORS['primary']}; color: white; padding: 20px 30px; text-align: left; border-bottom: 5px solid {COLORS['secondary']}; }}
                .dashboard-header h1 {{ margin: 0; font-weight: 700; }}
                .dashboard-header p {{ margin: 5px 0 0; font-weight: 300; }}
                .content-wrapper {{ padding: 20px; }}
                .card {{ background-color: {COLORS['card_background']}; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .card-header {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: {COLORS['primary']}; }}
                .data-source-text {{ font-size: 0.9em; color: {COLORS['light_text']}; margin-top: 10px; text-align: right; }}
                .control-panel {{ padding: 15px; background-color: {COLORS['card_background']}; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .dash-spreadsheet-container table {{ width: 100%; }}
                .dash-header {{ background-color: {COLORS['secondary']}; color: white; font-weight: bold; }}
                .dash-cell {{ text-align: left; padding: 8px; }}
                .Select-control, .select-input {{ border-radius: 3px; }} /* Added .select-input for dcc.Input */
                .Select-menu-outer {{ border-radius: 3px; }}
                .btn-primary {{ background-color: {COLORS['primary']}; border-color: {COLORS['primary']}; }}
                .btn-primary:hover {{ background-color: {COLORS['secondary']}; border-color: {COLORS['secondary']}; }}
                /* Custom input style */
                .custom-input {{
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 6px 12px;
                    width: 100%;
                    box-sizing: border-box; /* Ensures padding doesn't affect overall width */
                }}
            </style>
        </head>
        <body>
            {{%app_entry%}}
            <footer>
                {{%config%}}
                {{%scripts%}}
                {{%renderer%}}
            </footer>
        </body>
    </html>
    '''

    app.layout = html.Div([
        dcc.Store(id='store-reddit-data'),
        dcc.Store(id='store-data-source'),

        html.Div(className='dashboard-header', children=[
            html.H1("Reddit Trends Dashboard"),
            html.P("Visualisez les tendances et discussions Reddit pour des informations commerciales")
        ]),

        html.Div(className='content-wrapper', children=[
            # --- Row for Controls and KPIs ---
            html.Div(className='row', children=[
                # Control Panel
                html.Div(className='col-md-3', children=[
                    html.Div(className='control-panel card', children=[
                        html.H5("Contrôles Généraux", className="card-header"),
                        html.Label("Sélectionner la période :"),
                        dcc.Dropdown(
                            id='time-period-dropdown',
                            options=[
                                {'label': 'Aujourd\'hui (Dernier Fichier)', 'value': 'day'},
                                {'label': '7 Derniers Jours', 'value': 'week'},
                                {'label': '30 Derniers Jours', 'value': 'month'},
                                {'label': 'Depuis le Début', 'value': 'all'}
                            ],
                            value='day', clearable=False
                        ),
                        html.Br(),
                        html.Label("Filtrer par Subreddit :"),
                        dcc.Dropdown(id='subreddit-filter-dropdown', multi=True, placeholder="Tous les Subreddits"),
                        html.Br(),
                        html.Button('Rafraîchir les Données', id='refresh-button', n_clicks=0, className='btn btn-primary btn-block mt-2'),
                        html.Div(id='data-source-display', className='data-source-text')
                    ]),
                    html.Div(className='control-panel card', children=[ # New control panel for keywords
                        html.H5("Analyse par Mots-clés", className="card-header"),
                        html.Label("Entrez les mots-clés (séparés par virgule) :"),
                        dcc.Input(id='keyword-input', type='text', placeholder='ex: marque, concurrent, problème', className='custom-input', debounce=True),
                        # debounce=True waits for user to stop typing
                    ]),
                ]),

                # KPIs
                html.Div(className='col-md-9', children=[
                    html.Div(className='row', children=[
                        html.Div(className='col-md-4', children=[html.Div(className='card text-center', children=[html.H4("Posts Totaux", className="card-header"), html.H2(id='kpi-total-posts', style={'color': COLORS['primary']})])]),
                        html.Div(className='col-md-4', children=[html.Div(className='card text-center', children=[html.H4("Score Moyen", className="card-header"), html.H2(id='kpi-avg-score', style={'color': COLORS['primary']})])]),
                        html.Div(className='col-md-4', children=[html.Div(className='card text-center', children=[html.H4("Comm. Moyens", className="card-header"), html.H2(id='kpi-avg-comments', style={'color': COLORS['primary']})])]),
                    ]),
                     # Row for General Graphs
                    html.Div(className='row', children=[
                         html.Div(className='col-md-12', children=[html.Div(className='card', children=[html.H5("Activité des Posts sur la Période", className="card-header"), dcc.Graph(id='posts-over-time-graph')])]),
                    ]),
                    html.Div(className='row', children=[
                        html.Div(className='col-md-6', children=[html.Div(className='card', children=[html.H5("Top Subreddits (par posts)", className="card-header"), dcc.Graph(id='top-subreddits-graph')])]),
                        html.Div(className='col-md-6', children=[html.Div(className='card', children=[html.H5("Score vs. Commentaires", className="card-header"), dcc.Graph(id='score-comments-scatter')])]),
                    ]),
                ]),
            ]),
            
            # --- Row for Keyword Analysis ---
            html.Div(className='row', id='keyword-analysis-row', style={'display': 'none'}, children=[ # Hidden by default
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Tendance des Mots-clés", className="card-header"),
                        dcc.Graph(id='keyword-trend-graph')
                    ])
                ]),
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Posts contenant les Mots-clés", className="card-header"),
                        dash_table.DataTable(
                            id='keyword-posts-table',
                            page_size=5,
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '10px', 'minWidth': '100px', 'width': '150px', 'maxWidth': '300px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif'},
                            style_data={'border': '1px solid #eee'},
                            filter_action="native", sort_action="native", sort_mode="multi",
                            style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ]),

            # --- Row for Main Data Table ---
            html.Div(className='row', children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Tableau de Données Global", className="card-header"),
                        dash_table.DataTable(
                            id='reddit-data-table',
                            page_size=10,
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '10px', 'minWidth': '100px', 'width': '150px', 'maxWidth': '300px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif'},
                            style_data={'border': '1px solid #eee'},
                            filter_action="native", sort_action="native", sort_mode="multi",
                            page_action="native", style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ])
        ])
    ])

    # --- Callbacks ---
    @app.callback(
        [Output('store-reddit-data', 'data'),
         Output('store-data-source', 'data'),
         Output('subreddit-filter-dropdown', 'options'),
         Output('subreddit-filter-dropdown', 'value')], # Keep this to reset on refresh
        [Input('refresh-button', 'n_clicks'),
         Input('time-period-dropdown', 'value')],
    )
    def update_stored_data(n_clicks, time_period):
        print(f"Callback update_stored_data triggered by: {callback_context.triggered_id} with period: {time_period}")
        df, data_source_info = load_data(time_period)
        
        subreddit_options = []
        if not df.empty and 'subreddit' in df.columns:
            subreddit_options = [{'label': sub, 'value': sub} for sub in sorted(df['subreddit'].unique())]
        
        # Ensure 'selftext' column exists for keyword search, even if empty
        if 'selftext' not in df.columns and not df.empty:
            df['selftext'] = ''
        elif df.empty and 'selftext' not in df.columns: # Handle case where df is empty from load_data
            temp_cols = list(df.columns) + ['selftext']
            df = pd.DataFrame(columns=temp_cols)


        return df.to_dict('records'), data_source_info, subreddit_options, [] 

    @app.callback(
        Output('data-source-display', 'children'),
        Input('store-data-source', 'data')
    )
    def display_data_source(data_source_info):
        return f"Source: {data_source_info}" if data_source_info else "Source: N/A"

    @app.callback(
        [Output('kpi-total-posts', 'children'),
         Output('kpi-avg-score', 'children'),
         Output('kpi-avg-comments', 'children'),
         Output('posts-over-time-graph', 'figure'),
         Output('top-subreddits-graph', 'figure'),
         Output('score-comments-scatter', 'figure'),
         Output('reddit-data-table', 'data'),
         Output('reddit-data-table', 'columns'),
         # Outputs for keyword analysis
         Output('keyword-trend-graph', 'figure'),
         Output('keyword-posts-table', 'data'),
         Output('keyword-posts-table', 'columns'),
         Output('keyword-analysis-row', 'style')], # To show/hide the keyword section
        [Input('store-reddit-data', 'data'),
         Input('subreddit-filter-dropdown', 'value'),
         Input('keyword-input', 'value')] # New input for keywords
    )
    def update_visualizations_and_keyword_analysis(stored_data, selected_subreddits, keywords_str):
        # Default empty states
        empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Aucune donnée disponible', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}]}}
        empty_table_data = []
        default_table_cols = []
        kpi_default = "0"

        if not stored_data:
            return kpi_default, kpi_default, kpi_default, empty_fig, empty_fig, empty_fig, empty_table_data, default_table_cols, \
                   empty_fig, empty_table_data, default_table_cols, {'display': 'none'}

        df = pd.DataFrame(stored_data)
        if df.empty:
            return kpi_default, kpi_default, kpi_default, empty_fig, empty_fig, empty_fig, empty_table_data, default_table_cols, \
                   empty_fig, empty_table_data, default_table_cols, {'display': 'none'}
        
        default_table_cols = [{"name": i, "id": i} for i in df.columns if i != 'selftext'] # Exclude selftext from main table by default

        # Apply subreddit filter
        filtered_df = df.copy()
        if selected_subreddits: 
            filtered_df = filtered_df[filtered_df['subreddit'].isin(selected_subreddits)]
        
        if filtered_df.empty and selected_subreddits: # If filter results in empty
            no_filter_match_text = "Aucune donnée ne correspond au filtre de subreddit."
            empty_fig_filtered = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': no_filter_match_text, 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}]}}
            return kpi_default, kpi_default, kpi_default, empty_fig_filtered, empty_fig_filtered, empty_fig_filtered, empty_table_data, default_table_cols, \
                   empty_fig, empty_table_data, default_table_cols, {'display': 'none'}
        
        # If filtered_df becomes empty due to subreddits, but there *was* data initially.
        # If no subreddits selected, or subreddits selected but df is still populated:
        active_df = filtered_df if not filtered_df.empty else df # Use df if filter made it empty but no subreddits specified, else use filtered_df

        # KPIs
        total_posts = len(active_df)
        avg_score = round(active_df['score'].mean(), 1) if total_posts > 0 else 0
        avg_comments = round(active_df['num_comments'].mean(), 1) if total_posts > 0 else 0

        # Posts Over Time graph
        time_col_for_graph = 'created_utc'
        if 'file_date' in active_df.columns and active_df['file_date'].nunique() > 1:
            time_col_for_graph = 'file_date'
            posts_over_time_df = active_df.groupby(time_col_for_graph).size().reset_index(name='count')
            posts_over_time_df[time_col_for_graph] = pd.to_datetime(posts_over_time_df[time_col_for_graph])
            posts_over_time_df = posts_over_time_df.sort_values(time_col_for_graph)
        else:
            active_df['hour'] = pd.to_datetime(active_df['created_utc']).dt.floor('H')
            posts_over_time_df = active_df.groupby('hour').size().reset_index(name='count')
            posts_over_time_df = posts_over_time_df.sort_values('hour')
            time_col_for_graph = 'hour'
        
        fig_posts_over_time = px.line(posts_over_time_df, x=time_col_for_graph, y='count', markers=True, title="Nombre de Posts")
        fig_posts_over_time.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'])
        fig_posts_over_time.update_traces(line_color=COLORS['primary'])

        # Top Subreddits graph
        top_subreddits = active_df['subreddit'].value_counts().nlargest(10).reset_index()
        top_subreddits.columns = ['subreddit', 'count']
        fig_top_subreddits = px.bar(top_subreddits, x='subreddit', y='count', color='subreddit', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_top_subreddits.update_layout(showlegend=False, plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'])

        # Score vs. Comments scatter plot
        sample_size_scatter = min(1000, len(active_df))
        df_scatter = active_df.sample(sample_size_scatter) if sample_size_scatter > 0 else active_df
        fig_score_comments = px.scatter(df_scatter, x='score', y='num_comments', 
                                        color='subreddit' if 'subreddit' in df_scatter.columns and df_scatter['subreddit'].nunique() > 1 else None,
                                        hover_data=['title'], opacity=0.6, color_discrete_sequence=px.colors.qualitative.Set2)
        fig_score_comments.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'])
        if 'subreddit' not in df_scatter.columns or df_scatter['subreddit'].nunique() <= 1 :
             fig_score_comments.update_traces(marker=dict(color=COLORS['secondary']))
        
        # Main Data Table
        main_table_cols = [{"name": i, "id": i} for i in active_df.columns if i not in ['selftext', 'hour']] # Exclude selftext and temp hour col
        main_table_data = active_df.drop(columns=['selftext', 'hour'], errors='ignore').to_dict('records')


        # --- Keyword Analysis ---
        fig_keyword_trend = empty_fig
        keyword_table_data = empty_table_data
        keyword_table_cols = default_table_cols # Use general columns
        keyword_section_style = {'display': 'none'} # Hidden by default

        if keywords_str: # If keywords are provided
            keywords = [kw.strip().lower() for kw in keywords_str.split(',') if kw.strip()]
            if keywords:
                keyword_section_style = {'display': 'flex'} # Show the section (flex for row)
                
                # Create a regex pattern to find any of the keywords, case insensitive
                # Ensure keywords are escaped for regex if they contain special characters
                regex_keywords = [re.escape(kw) for kw in keywords]
                pattern = r'(' + '|'.join(regex_keywords) + r')'
                
                # Search in 'title' and 'selftext'. Ensure 'selftext' exists.
                df_keywords_found = active_df[
                    active_df['title'].str.contains(pattern, case=False, regex=True) |
                    active_df['selftext'].str.contains(pattern, case=False, regex=True)
                ]

                if not df_keywords_found.empty:
                    # Keyword Trend Graph
                    time_col_kw = 'created_utc'
                    if 'file_date' in df_keywords_found.columns and df_keywords_found['file_date'].nunique() > 1:
                        time_col_kw = 'file_date'
                        kw_trend_df = df_keywords_found.groupby(time_col_kw).size().reset_index(name='mentions')
                        kw_trend_df[time_col_kw] = pd.to_datetime(kw_trend_df[time_col_kw])
                        kw_trend_df = kw_trend_df.sort_values(time_col_kw)
                    else:
                        df_keywords_found_copy = df_keywords_found.copy() # Avoid SettingWithCopyWarning
                        df_keywords_found_copy.loc[:, 'hour_kw'] = pd.to_datetime(df_keywords_found_copy['created_utc']).dt.floor('H')
                        kw_trend_df = df_keywords_found_copy.groupby('hour_kw').size().reset_index(name='mentions')
                        kw_trend_df = kw_trend_df.sort_values('hour_kw')
                        time_col_kw = 'hour_kw'
                    
                    fig_keyword_trend = px.line(kw_trend_df, x=time_col_kw, y='mentions', markers=True, title=f"Mentions pour: {', '.join(keywords)}")
                    fig_keyword_trend.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'])
                    fig_keyword_trend.update_traces(line_color=COLORS['accent'])

                    # Keyword Posts Table
                    keyword_table_cols_list = ['title', 'subreddit', 'score', 'num_comments', 'created_utc', 'author', 'permalink']
                    # Ensure all columns exist, if not, use available ones from df_keywords_found
                    keyword_table_cols_final = [col for col in keyword_table_cols_list if col in df_keywords_found.columns]
                    
                    keyword_table_cols = [{"name": i, "id": i} for i in keyword_table_cols_final]
                    keyword_table_data = df_keywords_found[keyword_table_cols_final].to_dict('records')
                else: # No keywords found
                     fig_keyword_trend = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': f"Aucun post trouvé pour: {', '.join(keywords)}", 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}]}}


        return (f"{total_posts:,}", f"{avg_score:,}", f"{avg_comments:,}",
                fig_posts_over_time, fig_top_subreddits, fig_score_comments,
                main_table_data, main_table_cols,
                fig_keyword_trend, keyword_table_data, keyword_table_cols, keyword_section_style)

    return app

if __name__ == '__main__':
    from flask import Flask
    flask_server = Flask(__name__)
    app = create_dashboard(flask_server)
    app.run_server(debug=True, port=8050)
