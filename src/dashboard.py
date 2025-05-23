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
import re
from src.data_processing import load_data
from src.trend_detection import detect_trending_topics
from src.audience_segmentation import segment_audience
from src.competitive_analysis import analyze_competitive_mentions
from src.contextual_analysis import extract_context  # Importer la fonction d'analyse contextuelle
from src.predictive_analysis import train_predictive_model, predict_future_trends  # Importer les fonctions d'analyse prédictive

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
                    suppress_callback_exceptions=True, # Garder à True si vous avez des callbacks sur des composants générés dynamiquement
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
                .dashboard-header h1 {{ margin: 0; font-weight: 700; font-size: 1.8rem; }}
                .dashboard-header p {{ margin: 5px 0 0; font-weight: 300; font-size: 0.9rem;}}
                .content-wrapper {{ padding: 20px; }}
                .card {{ background-color: {COLORS['card_background']}; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .card-header {{ font-size: 1.1em; font-weight: bold; margin-bottom: 10px; color: {COLORS['primary']}; border-bottom: 1px solid #eee; padding-bottom: 8px;}}
                .data-source-text {{ font-size: 0.8em; color: {COLORS['light_text']}; margin-top: 10px; text-align: right; }}
                .control-panel {{ padding: 15px; background-color: {COLORS['card_background']}; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .dash-spreadsheet-container table {{ width: 100%; }}
                .dash-header {{ background-color: {COLORS['secondary']}; color: white; font-weight: bold; }}
                .dash-cell {{ text-align: left; padding: 8px; font-size:0.9rem; }}
                .Select-control, .select-input {{ border-radius: 3px; }}
                .Select-menu-outer {{ border-radius: 3px; }}
                .btn-primary {{ background-color: {COLORS['primary']}; border-color: {COLORS['primary']}; width: 100%; }}
                .btn-primary:hover {{ background-color: {COLORS['secondary']}; border-color: {COLORS['secondary']}; }}
                .custom-input {{
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 6px 12px;
                    width: 100%;
                    box-sizing: border-box;
                }}
                label {{ /* Style pour les labels des dropdowns/inputs */
                    font-weight: 500;
                    margin-bottom: .3rem;
                    font-size: 0.9rem;
                    color: {COLORS['text']};
                }}
                 .trending-topics-text {{
                    padding: 10px;
                    background-color: #f9f9f9;
                    border: 1px solid #eee;
                    border-radius: 4px;
                    min-height: 50px;
                    color: {COLORS['text']};
                    font-size: 0.9rem;
                    line-height: 1.5;
                }}
                /* Style pour les KPIs */
                .kpi-value {{
                    font-size: 1.8rem; /* Taille de la valeur KPI */
                    font-weight: 700;
                    color: {COLORS['primary']};
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
                        html.Button('Rafraîchir les Données', id='refresh-button', n_clicks=0, className='btn btn-primary mt-2'), # enlevé btn-block
                        html.Div(id='data-source-display', className='data-source-text')
                    ]),
                    html.Div(className='control-panel card', children=[
                        html.H5("Analyse par Mots-clés", className="card-header"),
                        html.Label("Mots-clés généraux (séparés par virgule) :"),
                        dcc.Input(id='keyword-input', type='text', placeholder='ex: produit, fonctionnalité...', className='custom-input', debounce=True),
                    ]),
                    html.Div(className='control-panel card', children=[
                        html.H5("Analyse Concurrentielle", className="card-header"),
                        html.Label("Concurrents/marques à suivre (séparés par virgule) :"),
                        dcc.Input(id='competitor-keyword-input', type='text', placeholder='ex: concurrent A, marque B', className='custom-input', debounce=True),
                    ]),
                ]),

                # KPIs
                html.Div(className='col-md-9', children=[
                    html.Div(className='row', children=[
                        html.Div(className='col-md-4', children=[html.Div(className='card text-center', children=[html.H4("Posts Totaux", className="card-header"), html.Div(id='kpi-total-posts', className='kpi-value')])]),
                        html.Div(className='col-md-4', children=[html.Div(className='card text-center', children=[html.H4("Score Moyen", className="card-header"), html.Div(id='kpi-avg-score', className='kpi-value')])]),
                        html.Div(className='col-md-4', children=[html.Div(className='card text-center', children=[html.H4("Comm. Moyens", className="card-header"), html.Div(id='kpi-avg-comments', className='kpi-value')])]),
                    ]),
                     # Row for General Graphs
                    html.Div(className='row', children=[
                         html.Div(className='col-md-12', children=[html.Div(className='card', children=[html.H5("Activité des Posts sur la Période", className="card-header"), dcc.Graph(id='posts-over-time-graph', config={'displayModeBar': False})])]),
                    ]),
                    html.Div(className='row', children=[
                        html.Div(className='col-md-6', children=[html.Div(className='card', children=[html.H5("Top Subreddits (par posts)", className="card-header"), dcc.Graph(id='top-subreddits-graph', config={'displayModeBar': False})])]),
                        html.Div(className='col-md-6', children=[html.Div(className='card', children=[html.H5("Score vs. Commentaires", className="card-header"), dcc.Graph(id='score-comments-scatter', config={'displayModeBar': False})])]),
                    ]),
                ]),
            ]),

            # --- Row for Sentiment Analysis ---
            html.Div(className='row', children=[
                html.Div(className='col-md-6', children=[
                    html.Div(className='card', children=[
                        html.H5("Distribution du Sentiment", className="card-header"),
                        dcc.Graph(id='sentiment-distribution-graph', config={'displayModeBar': False})
                    ])
                ]),
                html.Div(className='col-md-6', children=[
                    html.Div(className='card', children=[
                        html.H5("Sentiment Moyen par Subreddit (Top 10)", className="card-header"),
                        dcc.Graph(id='sentiment-by-subreddit-graph', config={'displayModeBar': False})
                    ])
                ]),
            ]),

            html.Div(className='row', children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Évolution du Sentiment Moyen", className="card-header"),
                        dcc.Graph(id='sentiment-over-time-graph', config={'displayModeBar': False})
                    ])
                ]),
            ]),

            # --- Row for Keyword Analysis (general) ---
            html.Div(className='row', id='keyword-analysis-row', style={'display': 'none'}, children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Tendance des Mots-clés Généraux", className="card-header"),
                        dcc.Graph(id='keyword-trend-graph', config={'displayModeBar': False})
                    ])
                ]),
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Posts contenant les Mots-clés Généraux", className="card-header"),
                        dash_table.DataTable(
                            id='keyword-posts-table', page_size=5,
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '8px', 'minWidth': '100px', 'width': '150px', 'maxWidth': '250px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif', 'fontSize':'0.85rem'},
                            style_data={'border': '1px solid #eee'}, filter_action="native", sort_action="native", sort_mode="multi",
                            style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ]),

            # --- Row for Competitive Analysis ---
            html.Div(className='row', id='competitive-analysis-row', style={'display': 'none'}, children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Analyse des Mentions Concurrentielles", className="card-header"),
                        dash_table.DataTable(
                            id='competitive-analysis-table', page_size=5,
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '8px', 'minWidth': '120px', 'width': '180px', 'maxWidth': '250px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif', 'fontSize':'0.85rem'},
                            style_data={'border': '1px solid #eee'}, filter_action="native", sort_action="native", sort_mode="multi",
                            style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ]),

            # --- Row for Trending Topics & Audience Segmentation ---
            html.Div(className='row', children=[
                 html.Div(className='col-md-4', children=[ # Trending topics prennent moins de place
                    html.Div(className='card', style={'height': 'calc(100% - 20px)'}, children=[ # Ajuster height pour alignement si nécessaire
                        html.H5("Sujets en Croissance (Mots)", className="card-header"),
                        html.Div(id='trending-topics-display', className='trending-topics-text')
                    ])
                ]),
                html.Div(className='col-md-8', children=[
                    html.Div(className='card', children=[
                        html.H5("Segmentation de l'Audience (par Auteur)", className="card-header"),
                        dash_table.DataTable(
                            id='audience-segmentation-table', page_size=5, # Réduit pour s'adapter à côté des trending topics
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '8px', 'minWidth': '100px', 'width': '120px', 'maxWidth': '200px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif', 'fontSize':'0.85rem'},
                            style_data={'border': '1px solid #eee'}, filter_action="native", sort_action="native", sort_mode="multi",
                            style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ]),

            # --- Row for Main Data Table ---
            html.Div(className='row', children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Tableau de Données Détaillé", className="card-header"),
                        dash_table.DataTable(
                            id='reddit-data-table', page_size=10,
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '8px', 'minWidth': '100px', 'width': '150px', 'maxWidth': '250px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif', 'fontSize':'0.85rem'},
                            style_data={'border': '1px solid #eee'}, filter_action="native", sort_action="native", sort_mode="multi",
                            page_action="native", style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ]),

            # --- Row for Contextual Analysis ---
            html.Div(className='row', id='contextual-analysis-row', style={'display': 'none'}, children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Analyse Contextuelle des Mots-clés", className="card-header"),
                        dash_table.DataTable(
                            id='contextual-analysis-table', page_size=5,
                            style_header={'backgroundColor': COLORS['secondary'], 'color': 'white', 'fontWeight': 'bold'},
                            style_cell={'textAlign': 'left', 'padding': '8px', 'minWidth': '120px', 'width': '180px', 'maxWidth': '250px',
                                        'whiteSpace': 'normal', 'height': 'auto', 'fontFamily': 'Roboto, sans-serif', 'fontSize':'0.85rem'},
                            style_data={'border': '1px solid #eee'}, filter_action="native", sort_action="native", sort_mode="multi",
                            style_table={'overflowX': 'auto'},
                        )
                    ])
                ])
            ]),

            # --- Row for Predictive Analysis ---
            html.Div(className='row', id='predictive-analysis-row', style={'display': 'none'}, children=[
                html.Div(className='col-md-12', children=[
                    html.Div(className='card', children=[
                        html.H5("Analyse Prédictive des Tendances", className="card-header"),
                        dcc.Graph(id='predictive-trends-graph', config={'displayModeBar': False})
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
         Output('subreddit-filter-dropdown', 'value')],
        [Input('refresh-button', 'n_clicks'),
         Input('time-period-dropdown', 'value')],
    )
    def update_stored_data(n_clicks, time_period):
        # Le print peut être commenté en production
        # print(f"Callback update_stored_data triggered by: {callback_context.triggered_id} with period: {time_period}")
        df, data_source_info = load_data(time_period)

        subreddit_options = []
        if not df.empty and 'subreddit' in df.columns:
            # S'assurer que les valeurs sont uniques et triées
            unique_subreddits = sorted(list(df['subreddit'].unique()))
            subreddit_options = [{'label': sub, 'value': sub} for sub in unique_subreddits]

        # S'assurer que 'selftext' existe pour éviter des erreurs en aval
        if not df.empty and 'selftext' not in df.columns:
            df['selftext'] = ''
        elif df.empty: # Si le df est vide après chargement
            # S'assurer que les colonnes attendues par les callbacks existent même si le df est vide
            expected_cols = ['title', 'selftext', 'subreddit', 'score', 'num_comments', 'created_utc', 'author', 'permalink', 'file_date',
                             'sentiment_category', 'sentiment_compound'] # Ajouter d'autres colonnes essentielles si nécessaire
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None # Ou pd.NA
            # df = pd.DataFrame(columns=expected_cols) # Alternative: recréer un df vide avec les bonnes colonnes

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
         Output('keyword-trend-graph', 'figure'),
         Output('keyword-posts-table', 'data'),
         Output('keyword-posts-table', 'columns'),
         Output('keyword-analysis-row', 'style'),
         Output('sentiment-distribution-graph', 'figure'),
         Output('sentiment-by-subreddit-graph', 'figure'),
         Output('sentiment-over-time-graph', 'figure'),
         Output('trending-topics-display', 'children'),
         Output('audience-segmentation-table', 'data'),
         Output('audience-segmentation-table', 'columns'),
         Output('competitive-analysis-table', 'data'),
         Output('competitive-analysis-table', 'columns'),
         Output('competitive-analysis-row', 'style'),
         Output('contextual-analysis-table', 'data'),
         Output('contextual-analysis-table', 'columns'),
         Output('contextual-analysis-row', 'style'),
         Output('predictive-trends-graph', 'figure'),
         Output('predictive-analysis-row', 'style')
        ],
        [Input('store-reddit-data', 'data'),
         Input('subreddit-filter-dropdown', 'value'),
         Input('keyword-input', 'value'),
         Input('competitor-keyword-input', 'value')]
    )
    def update_all_visualizations(stored_data, selected_subreddits, keywords_str, competitor_keywords_str):
        # Default empty states
        empty_fig = go.Figure()
        empty_fig.update_layout(
            xaxis={'visible': False}, yaxis={'visible': False},
            annotations=[{'text': 'Aucune donnée à afficher', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}],
            plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background']
        )
        empty_table_data = []
        base_cols_for_empty_tables = [{"name": "Info", "id": "Info"}] # Pour éviter les erreurs avec des tables vides
        kpi_default = "0"
        hidden_section_style = {'display': 'none'}

        if not stored_data:
            return kpi_default, kpi_default, kpi_default, empty_fig, empty_fig, empty_fig, empty_table_data, base_cols_for_empty_tables, \
                   empty_fig, empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_fig, empty_fig, empty_fig, "Aucun sujet en croissance détecté.", \
                   empty_table_data, base_cols_for_empty_tables, \
                   empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_fig, hidden_section_style

        df = pd.DataFrame(stored_data)
        if df.empty or all(col not in df.columns for col in ['title', 'score', 'num_comments', 'created_utc']): # Vérifier les colonnes essentielles
            return kpi_default, kpi_default, kpi_default, empty_fig, empty_fig, empty_fig, empty_table_data, base_cols_for_empty_tables, \
                   empty_fig, empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_fig, empty_fig, empty_fig, "Données insuffisantes ou corrompues.", \
                   empty_table_data, base_cols_for_empty_tables, \
                   empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_fig, hidden_section_style

        # Assurer que les colonnes de sentiment existent, sinon les initialiser (au cas où add_sentiment_analysis n'aurait pas pu les créer)
        for sent_col in ['sentiment_category', 'sentiment_compound']:
            if sent_col not in df.columns:
                df[sent_col] = 'N/A' if sent_col == 'sentiment_category' else 0.0
        if 'selftext' not in df.columns: df['selftext'] = ''

        # Apply subreddit filter
        filtered_df = df.copy()
        if selected_subreddits: # Doit être une liste non vide
            filtered_df = filtered_df[filtered_df['subreddit'].isin(selected_subreddits)]

        # Si le filtrage par subreddit vide le DataFrame, mais que des subreddits étaient bien sélectionnés
        if filtered_df.empty and selected_subreddits:
            no_filter_match_text = "Aucune donnée ne correspond au filtre de subreddit."
            empty_fig_filtered = go.Figure()
            empty_fig_filtered.update_layout(xaxis={'visible': False}, yaxis={'visible': False}, annotations=[{'text': no_filter_match_text, 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}], plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'])
            return kpi_default, kpi_default, kpi_default, empty_fig_filtered, empty_fig_filtered, empty_fig_filtered, empty_table_data, base_cols_for_empty_tables, \
                   empty_fig, empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_fig, empty_fig, empty_fig, "Aucun sujet en croissance pour ce filtre.", \
                   empty_table_data, base_cols_for_empty_tables, \
                   empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_table_data, base_cols_for_empty_tables, hidden_section_style, \
                   empty_fig, hidden_section_style

        active_df = filtered_df # Utiliser filtered_df après le filtre (peut être égal à df si aucun filtre)

        # KPIs
        total_posts = len(active_df)
        avg_score = round(active_df['score'].mean(), 1) if total_posts > 0 and pd.notna(active_df['score'].mean()) else 0
        avg_comments = round(active_df['num_comments'].mean(), 1) if total_posts > 0 and pd.notna(active_df['num_comments'].mean()) else 0

        # --- Posts Over Time graph ---
        fig_posts_over_time = empty_fig
        if total_posts > 0:
            active_df_for_time_graph = active_df.copy()
            if 'file_date' in active_df_for_time_graph.columns and active_df_for_time_graph['file_date'].nunique() > 1:
                time_col_for_graph = 'file_date'
                posts_over_time_df = active_df_for_time_graph.groupby(time_col_for_graph).size().reset_index(name='count')
                posts_over_time_df[time_col_for_graph] = pd.to_datetime(posts_over_time_df[time_col_for_graph])
            else:
                active_df_for_time_graph['hour'] = pd.to_datetime(active_df_for_time_graph['created_utc']).dt.floor('h')
                time_col_for_graph = 'hour'
                posts_over_time_df = active_df_for_time_graph.groupby(time_col_for_graph).size().reset_index(name='count')

            posts_over_time_df = posts_over_time_df.sort_values(time_col_for_graph)
            fig_posts_over_time = px.line(posts_over_time_df, x=time_col_for_graph, y='count', markers=True, title="Nombre de Posts")
            fig_posts_over_time.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'], margin=dict(t=50, b=20, l=30, r=30))
            fig_posts_over_time.update_traces(line_color=COLORS['primary'])

        # --- Top Subreddits graph ---
        fig_top_subreddits = empty_fig
        if total_posts > 0 and 'subreddit' in active_df.columns:
            top_subreddits_data = active_df['subreddit'].value_counts().nlargest(10).reset_index()
            top_subreddits_data.columns = ['subreddit', 'count']
            fig_top_subreddits = px.bar(top_subreddits_data, x='subreddit', y='count', color='subreddit', color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_top_subreddits.update_layout(showlegend=False, plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'], margin=dict(t=50, b=20, l=30, r=30))

        # --- Score vs. Comments scatter plot ---
        fig_score_comments = empty_fig
        if total_posts > 0:
            sample_size_scatter = min(1000, len(active_df))
            df_scatter = active_df.sample(sample_size_scatter) if sample_size_scatter > 0 else active_df
            fig_score_comments = px.scatter(df_scatter, x='score', y='num_comments',
                                            color='subreddit' if 'subreddit' in df_scatter.columns and df_scatter['subreddit'].nunique() > 1 else None,
                                            hover_data=['title'], opacity=0.6, color_discrete_sequence=px.colors.qualitative.Set2)
            fig_score_comments.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'], margin=dict(t=50, b=20, l=30, r=30))
            if 'subreddit' not in df_scatter.columns or df_scatter['subreddit'].nunique() <= 1:
                fig_score_comments.update_traces(marker=dict(color=COLORS['secondary']))

        # --- Main Data Table ---
        main_table_cols_to_drop = ['selftext']
        # Ajouter les colonnes temporaires créées dynamiquement pour les graphiques si elles existent
        for temp_col in ['hour', 'hour_kw', 'hour_sentiment']:
            if temp_col in active_df.columns:
                main_table_cols_to_drop.append(temp_col)
        if 'file_date_dt' in active_df.columns: main_table_cols_to_drop.append('file_date_dt')

        main_table_cols_display = [{"name": i, "id": i} for i in active_df.columns if i not in main_table_cols_to_drop]
        main_table_data_display = active_df.drop(columns=main_table_cols_to_drop, errors='ignore').to_dict('records')

        # --- Keyword Analysis (General) ---
        fig_keyword_trend = empty_fig
        keyword_table_data_display = empty_table_data
        keyword_table_cols_display_struct = base_cols_for_empty_tables
        keyword_section_style_display = hidden_section_style

        if keywords_str and total_posts > 0:
            keywords = [kw.strip().lower() for kw in keywords_str.split(',') if kw.strip()]
            if keywords:
                keyword_section_style_display = {'display': 'flex'}
                regex_keywords = [re.escape(kw) for kw in keywords]
                pattern = r'(' + '|'.join(regex_keywords) + r')'

                df_keywords_found = active_df[
                    active_df['title'].str.contains(pattern, case=False, regex=True) |
                    active_df['selftext'].str.contains(pattern, case=False, regex=True)
                ]
                if not df_keywords_found.empty:
                    active_df_for_kw_trend = df_keywords_found.copy()
                    if 'file_date' in active_df_for_kw_trend.columns and active_df_for_kw_trend['file_date'].nunique() > 1:
                        time_col_kw = 'file_date'
                        kw_trend_df = active_df_for_kw_trend.groupby(time_col_kw).size().reset_index(name='mentions')
                        kw_trend_df[time_col_kw] = pd.to_datetime(kw_trend_df[time_col_kw])
                    else:
                        active_df_for_kw_trend['hour_kw'] = pd.to_datetime(active_df_for_kw_trend['created_utc']).dt.floor('h')
                        time_col_kw = 'hour_kw'
                        kw_trend_df = active_df_for_kw_trend.groupby(time_col_kw).size().reset_index(name='mentions')

                    kw_trend_df = kw_trend_df.sort_values(time_col_kw)
                    fig_keyword_trend = px.line(kw_trend_df, x=time_col_kw, y='mentions', markers=True, title=f"Mentions pour: {', '.join(keywords)}")
                    fig_keyword_trend.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'], margin=dict(t=50, b=20, l=30, r=30))
                    fig_keyword_trend.update_traces(line_color=COLORS['accent'])

                    keyword_table_cols_list = ['title', 'subreddit', 'score', 'num_comments', 'created_utc', 'author', 'permalink']
                    keyword_table_cols_final = [col for col in keyword_table_cols_list if col in df_keywords_found.columns]
                    keyword_table_cols_display_struct = [{"name": i, "id": i} for i in keyword_table_cols_final]
                    keyword_table_data_display = df_keywords_found[keyword_table_cols_final].to_dict('records')
                else:
                    fig_keyword_trend.update_layout(annotations=[{'text': f"Aucun post trouvé pour les mots-clés: {', '.join(keywords)}", 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}])

        # --- Sentiment Analysis ---
        fig_sentiment_dist = empty_fig
        fig_sentiment_subreddit = empty_fig
        fig_sentiment_time = empty_fig

        if total_posts > 0 and 'sentiment_category' in active_df.columns and not active_df['sentiment_category'].empty:
            sentiment_counts = active_df['sentiment_category'].value_counts().reset_index()
            if not sentiment_counts.empty:
                sentiment_counts.columns = ['sentiment', 'count']
                fig_sentiment_dist = px.pie(sentiment_counts, values='count', names='sentiment',
                                            color='sentiment',
                                            color_discrete_map={'Positif': '#4CAF50', 'Neutre': '#FFC107', 'Négatif': '#F44336', 'N/A': '#9E9E9E'},
                                            title="Distribution du Sentiment")
                fig_sentiment_dist.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], margin=dict(t=50, b=20, l=30, r=30))

            if 'subreddit' in active_df.columns and 'sentiment_compound' in active_df.columns:
                # Exclure N/A pour le calcul de la moyenne du sentiment composé
                df_sentiment_valid = active_df[active_df['sentiment_compound'] != 0.0] # Ou une autre condition pour exclure les 'N/A' si encodés autrement
                if not df_sentiment_valid.empty:
                    top_subreddits_sentiment = df_sentiment_valid.groupby('subreddit')['sentiment_compound'].mean().nlargest(10).reset_index()
                    if not top_subreddits_sentiment.empty:
                        fig_sentiment_subreddit = px.bar(top_subreddits_sentiment, x='subreddit', y='sentiment_compound',
                                                    color='sentiment_compound',
                                                    color_continuous_scale=['#F44336', '#FFC107', '#4CAF50'], # Rouge, Jaune, Vert
                                                    range_color=[-1,1], # Assurer que l'échelle va de -1 à 1
                                                    title="Score de Sentiment Moyen")
                        fig_sentiment_subreddit.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], margin=dict(t=50, b=20, l=30, r=30))

            active_df_for_sentiment_time = active_df.copy() # Utiliser une copie pour ajouter des colonnes temporaires
            if 'file_date' in active_df_for_sentiment_time.columns and active_df_for_sentiment_time['file_date'].nunique() > 1:
                sentiment_time_df = active_df_for_sentiment_time.groupby('file_date')['sentiment_compound'].mean().reset_index()
                time_col_sentiment = 'file_date'
                sentiment_time_df[time_col_sentiment] = pd.to_datetime(sentiment_time_df[time_col_sentiment]) # Assurer que c'est datetime
            else:
                active_df_for_sentiment_time['hour_sentiment'] = pd.to_datetime(active_df_for_sentiment_time['created_utc']).dt.floor('h')
                sentiment_time_df = active_df_for_sentiment_time.groupby('hour_sentiment')['sentiment_compound'].mean().reset_index()
                time_col_sentiment = 'hour_sentiment'

            if not sentiment_time_df.empty:
                sentiment_time_df = sentiment_time_df.sort_values(time_col_sentiment) # Trier par date/heure
                fig_sentiment_time = px.line(sentiment_time_df, x=time_col_sentiment, y='sentiment_compound', title="Évolution du Sentiment Moyen")
                fig_sentiment_time.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], margin=dict(t=50, b=20, l=30, r=30))
                fig_sentiment_time.add_hline(y=0, line_dash="dash", line_color="gray") # Ligne pour sentiment neutre
                fig_sentiment_time.update_yaxes(range=[-1, 1]) # Sentiment composé est entre -1 et 1

        # --- Trending Topics ---
        trending_topics_list_display = "Aucun sujet en croissance détecté."
        if total_posts > 0:
            trending_topics_list = detect_trending_topics(active_df.copy(), time_window='day')
            if trending_topics_list:
                 trending_topics_list_display = ", ".join(trending_topics_list[:15]) # Limiter à 15 pour l'affichage
                 if len(trending_topics_list) > 15:
                    trending_topics_list_display += "..."

        # --- Audience Segmentation ---
        audience_segmentation_data_display = empty_table_data
        audience_segmentation_cols_display = base_cols_for_empty_tables
        if total_posts > 0:
            audience_segmentation_df = segment_audience(active_df.copy())
            if not audience_segmentation_df.empty:
                audience_segmentation_cols_display = [{"name": i, "id": i} for i in audience_segmentation_df.columns]
                audience_segmentation_data_display = audience_segmentation_df.to_dict('records')

        # --- Competitive Analysis ---
        competitive_analysis_data_display = empty_table_data
        competitive_analysis_cols_display = base_cols_for_empty_tables
        competitive_analysis_section_style_display = hidden_section_style

        if competitor_keywords_str and total_posts > 0:
            competitor_keywords = [kw.strip().lower() for kw in competitor_keywords_str.split(',') if kw.strip()]
            if competitor_keywords:
                competitive_analysis_section_style_display = {'display': 'flex'}
                df_competitive = analyze_competitive_mentions(active_df.copy(), competitor_keywords)
                if not df_competitive.empty:
                    competitive_analysis_cols_display = [{"name": i, "id": i} for i in df_competitive.columns]
                    competitive_analysis_data_display = df_competitive.to_dict('records')
                # Si df_competitive est vide, la section sera affichée mais le tableau sera vide ou avec le message par défaut.

        # --- Contextual Analysis ---
        contextual_analysis_data_display = empty_table_data
        contextual_analysis_cols_display = base_cols_for_empty_tables
        contextual_analysis_section_style_display = hidden_section_style

        if keywords_str and total_posts > 0:
            keywords = [kw.strip().lower() for kw in keywords_str.split(',') if kw.strip()]
            if keywords:
                contextual_analysis_section_style_display = {'display': 'flex'}
                contextual_analysis_list = []
                for index, row in active_df.iterrows():
                    title_context = extract_context(row['title'], keywords)
                    selftext_context = extract_context(row['selftext'], keywords)
                    combined_context = title_context + selftext_context
                    for context in combined_context:
                        contextual_analysis_list.append({
                            'post_id': row['id'],
                            'title': row['title'],
                            'context': context,
                            'subreddit': row['subreddit'],
                            'score': row['score'],
                            'num_comments': row['num_comments'],
                            'created_utc': row['created_utc'],
                            'author': row['author'],
                            'permalink': row['permalink']
                        })

                if contextual_analysis_list:
                    contextual_analysis_df = pd.DataFrame(contextual_analysis_list)
                    contextual_analysis_cols_display = [{"name": i, "id": i} for i in contextual_analysis_df.columns]
                    contextual_analysis_data_display = contextual_analysis_df.to_dict('records')

        # --- Predictive Analysis ---
        predictive_trends_fig = empty_fig
        predictive_analysis_section_style_display = hidden_section_style

        if total_posts > 0:
            predictive_analysis_section_style_display = {'display': 'flex'}
            model = train_predictive_model(active_df)
            new_data = pd.DataFrame({'num_comments': [10, 20, 30, 40, 50]})  # Exemple de nouvelles données
            predictions = predict_future_trends(model, new_data)
            predictive_trends_df = pd.DataFrame({'num_comments': new_data['num_comments'], 'predicted_score': predictions})
            predictive_trends_fig = px.line(predictive_trends_df, x='num_comments', y='predicted_score', markers=True, title="Prédiction des Scores de Posts")
            predictive_trends_fig.update_layout(plot_bgcolor=COLORS['card_background'], paper_bgcolor=COLORS['card_background'], font_color=COLORS['text'], xaxis_gridcolor=COLORS['grid'], yaxis_gridcolor=COLORS['grid'], margin=dict(t=50, b=20, l=30, r=30))
            predictive_trends_fig.update_traces(line_color=COLORS['accent'])

        return (f"{total_posts:,}", f"{avg_score:,}", f"{avg_comments:,}",
                fig_posts_over_time, fig_top_subreddits, fig_score_comments,
                main_table_data_display, main_table_cols_display,
                fig_keyword_trend, keyword_table_data_display, keyword_table_cols_display_struct, keyword_section_style_display,
                fig_sentiment_dist, fig_sentiment_subreddit, fig_sentiment_time, trending_topics_list_display,
                audience_segmentation_data_display, audience_segmentation_cols_display,
                competitive_analysis_data_display, competitive_analysis_cols_display, competitive_analysis_section_style_display,
                contextual_analysis_data_display, contextual_analysis_cols_display, contextual_analysis_section_style_display,
                predictive_trends_fig, predictive_analysis_section_style_display)

    return app

if __name__ == '__main__':
    from flask import Flask
    flask_server = Flask(__name__)
    # Pour s'assurer que le chemin est correct lors de l'exécution directe (optionnel si la structure du projet est gérée par PYTHONPATH)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    app = create_dashboard(flask_server)
    app.run_server(debug=True, port=8050)

