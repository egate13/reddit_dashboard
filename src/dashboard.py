# /home/wmfs0449/reddit_dashboard/src/dashboard.py

import sys
import os

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import io
import re # For keyword searching
from src.data_processing import load_data
from src.trend_detection import detect_trending_topics
from src.audience_segmentation import segment_audience

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

            # --- Row for Sentiment Analysis ---
            html.Div(className='row', children=[
                html.Div(className='col-md-6', children=[
                    html.Div(className='card', children=[
                        html.H5("Distribution du Sentiment", className="card-header"),
                        dcc.Graph(id='sentiment-distribution-graph')
                    ])
                ]),
                html.Div(className='col-md-6', children=[
                    html.Div(className='card', children=[
                        html.H5("Sentiment par Subreddit", className="card-header"),
                        dcc.Graph(id='sentiment-by-subreddit-graph')
                    ])
                ]),
            ]),

            # --- Row for Sentiment Over Time ---
            html.Div(className='row', children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Évolution du Sentiment", className="card-header"),
                        dcc.Graph(id='sentiment-over-time-graph')
                    ])
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

            # --- Row for Trending Topics ---
            html.Div(className='row', children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Sujets en Croissance", className="card-header"),
                        html.Div(id='trending-topics-display', className='trending-topics-text')
                    ])
                ])
            ]),

            # --- Row for Audience Segmentation ---
            html.Div(className='row', children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Segmentation par Audience", className="card-header"),
                        dash_table.DataTable(
                            id='audience-segmentation-table',
                            page_size=10,
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
         Output('keyword-analysis-row', 'style'),
         # Outputs for sentiment analysis
         Output('sentiment-distribution-graph', 'figure'),
         Output('sentiment-by-subreddit-graph', 'figure'),
         Output('sentiment-over-time-graph', 'figure'),
         # Output for trending topics
         Output('trending-topics-display', 'children'),
         # Output for audience segmentation
         Output('audience-segmentation-table', 'data'),
         Output('audience-segmentation-table', 'columns')],
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
                   empty_fig, empty_table_data, default_table_cols, {'display': 'none'}, empty_fig, empty_fig, empty_fig, "Aucun sujet en croissance", empty_table_data, default_table_cols

        df = pd.DataFrame(stored_data)
        if df.empty:
            return kpi_default, kpi_default, kpi_default, empty_fig, empty_fig, empty_fig, empty_table_data, default_table_cols, \
                   empty_fig, empty_table_data, default_table_cols, {'display': 'none'}, empty_fig, empty_fig, empty_fig, "Aucun sujet en croissance", empty_table_data, default_table_cols

        default_table_cols = [{"name": i, "id": i} for i in df.columns if i != 'selftext'] # Exclude selftext from main table by default

        # Apply subreddit filter
        filtered_df = df.copy()
        if selected_subreddits:
            filtered_df = filtered_df[filtered_df['subreddit'].isin(selected_subreddits)]

        if filtered_df.empty and selected_subreddits: # If filter results in empty
            no_filter_match_text = "Aucune donnée ne correspond au filtre de subreddit."
            empty_fig_filtered = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': no_filter_match_text, 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}]}}
            return kpi_default, kpi_default, kpi_default, empty_fig_filtered, empty_fig_filtered, empty_fig_filtered, empty_table_data, default_table_cols, \
                   empty_fig, empty_table_data, default_table_cols, {'display': 'none'}, empty_fig, empty_fig, empty_fig, "Aucun sujet en croissance", empty_table_data, default_table_cols

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
        if 'subreddit' not in df_scatter.columns or df_scatter['subreddit'].nunique() <= 1:
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

        # --- Sentiment Analysis ---
        # Sentiment Distribution Graph
        sentiment_counts = active_df['sentiment_category'].value_counts().reset_index()
        sentiment_counts.columns = ['sentiment', 'count']
        fig_sentiment_dist = px.pie(sentiment_counts, values='count', names='sentiment',
                                     color='sentiment',
                                     color_discrete_map={'Positif': '#4CAF50', 'Neutre': '#FFC107', 'Négatif': '#F44336'},
                                     title="Distribution du Sentiment")
        fig_sentiment_dist.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'])

        # Sentiment by Subreddit
        top_subreddits_sentiment = active_df.groupby('subreddit')['sentiment_compound'].mean().nlargest(10).reset_index()
        fig_sentiment_subreddit = px.bar(top_subreddits_sentiment, x='subreddit', y='sentiment_compound',
                                       color='sentiment_compound',
                                       color_continuous_scale=['#F44336', '#FFC107', '#4CAF50'],
                                       title="Score de Sentiment Moyen par Subreddit")
        fig_sentiment_subreddit.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'])

        # Sentiment Over Time
        if 'file_date' in active_df.columns and active_df['file_date'].nunique() > 1:
            sentiment_time_df = active_df.groupby('file_date')['sentiment_compound'].mean().reset_index()
            time_col = 'file_date'
        else:
            active_df['hour'] = pd.to_datetime(active_df['created_utc']).dt.floor('H')
            sentiment_time_df = active_df.groupby('hour')['sentiment_compound'].mean().reset_index()
            time_col = 'hour'

        fig_sentiment_time = px.line(sentiment_time_df, x=time_col, y='sentiment_compound',
                                      title="Évolution du Sentiment dans le Temps")
        fig_sentiment_time.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'])
        fig_sentiment_time.add_hline(y=0, line_dash="dash", line_color="gray")

        # --- Trending Topics ---
        trending_topics = detect_trending_topics(active_df, time_window='day')
        trending_topics_display = ", ".join(trending_topics) if trending_topics else "Aucun sujet en croissance"

        # --- Audience Segmentation ---
        audience_segmentation_df = segment_audience(active_df)
        audience_segmentation_cols = [{"name": i, "id": i} for i in audience_segmentation_df.columns]
        audience_segmentation_data = audience_segmentation_df.to_dict('records')

        return (f"{total_posts:,}", f"{avg_score:,}", f"{avg_comments:,}",
                fig_posts_over_time, fig_top_subreddits, fig_score_comments,
                main_table_data, main_table_cols,
                fig_keyword_trend, keyword_table_data, keyword_table_cols, keyword_section_style,
                fig_sentiment_dist, fig_sentiment_subreddit, fig_sentiment_time, trending_topics_display,
                audience_segmentation_data, audience_segmentation_cols)

    return app

if __name__ == '__main__':
    from flask import Flask
    flask_server = Flask(__name__)
    app = create_dashboard(flask_server)
    app.run_server(debug=True, port=8050)

