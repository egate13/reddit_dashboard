# /home/wmfs0449/reddit_dashboard/src/competitive_analysis.py

import pandas as pd
import re

def analyze_competitive_mentions(df, keywords):
    """Analyse les mentions des marques/produits concurrents et les métriques d'engagement."""
    if df.empty or not keywords:
        return pd.DataFrame()

    # Créer une regex pattern pour trouver les mots-clés
    regex_keywords = [re.escape(kw) for kw in keywords]
    pattern = r'(' + '|'.join(regex_keywords) + r')'

    # Filtrer les posts contenant les mots-clés
    df_mentions = df[df['title'].str.contains(pattern, case=False, regex=True) |
                     df['selftext'].str.contains(pattern, case=False, regex=True)]

    if df_mentions.empty:
        return pd.DataFrame()

    # Extraire les mentions spécifiques
    df_mentions['mentions'] = df_mentions.apply(lambda row: [kw for kw in keywords if re.search(re.escape(kw), row['title'], re.IGNORECASE) or re.search(re.escape(kw), row['selftext'], re.IGNORECASE)], axis=1)

    # Calculer les métriques d'engagement
    df_mentions['engagement'] = df_mentions['score'] + df_mentions['num_comments']

    # Agrégat les données par mot-clé
    aggregated_data = df_mentions.explode('mentions').groupby('mentions').agg(
        mentions_count=('mentions', 'count'),
        avg_score=('score', 'mean'),
        avg_comments=('num_comments', 'mean'),
        total_engagement=('engagement', 'sum')
    ).reset_index()

    return aggregated_data

