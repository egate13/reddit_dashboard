# /home/wmfs0449/reddit_dashboard/src/audience_segmentation.py

import pandas as pd

def segment_audience(df):
    """Segmente les utilisateurs en fonction de leurs interactions avec les contenus."""
    if df.empty:
        return pd.DataFrame()

    # Analyser les interactions par utilisateur
    user_interactions = df.groupby('author').agg(
        total_posts=('author', 'count'),
        avg_score=('score', 'mean'),
        avg_comments=('num_comments', 'mean'),
        preferred_subreddits=('subreddit', lambda x: x.value_counts().index[0] if not x.empty else 'N/A')
    ).reset_index()

    # Classer les utilisateurs en segments (exemple simplifié)
    user_interactions['segment'] = pd.cut(user_interactions['total_posts'], bins=[0, 10, 50, 100, float('inf')], labels=['Inactif', 'Occasionnel', 'Actif', 'Très Actif'])

    return user_interactions

