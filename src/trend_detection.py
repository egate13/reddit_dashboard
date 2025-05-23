# /home/wmfs0449/reddit_dashboard/src/trend_detection.py

import pandas as pd
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Télécharger les ressources nécessaires (à exécuter une fois)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt_tab')
def detect_trending_topics(df, time_window='day'):
    """Détecte les sujets en croissance rapide dans les données Reddit."""
    if df.empty:
        return []

    # Nettoyer et tokeniser les textes
    stop_words = set(stopwords.words('english'))
    all_words = []

    for text in df['title'] + ' ' + df['selftext']:
        words = word_tokenize(text.lower())
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        all_words.extend(filtered_words)

    # Compter la fréquence des mots
    word_counts = Counter(all_words)

    # Filtrer les mots fréquents
    common_words = [word for word, count in word_counts.items() if count > 1]

    # Détecter les pics de fréquence
    trending_topics = []
    for word in common_words:
        word_df = df[df['title'].str.contains(word, case=False) | df['selftext'].str.contains(word, case=False)]
        if len(word_df) > 1:
            word_df['created_utc'] = pd.to_datetime(word_df['created_utc'])
            if time_window == 'day':
                word_df['hour'] = word_df['created_utc'].dt.floor('H')
                word_counts_by_time = word_df.groupby('hour').size()
            elif time_window == 'week':
                word_df['day'] = word_df['created_utc'].dt.floor('D')
                word_counts_by_time = word_df.groupby('day').size()
            else:
                word_counts_by_time = word_df.groupby('created_utc').size()

            if word_counts_by_time.max() > word_counts_by_time.mean() * 2:
                trending_topics.append(word)

    return trending_topics

