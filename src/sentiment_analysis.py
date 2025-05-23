# /home/wmfs0449/reddit_dashboard/src/sentiment_analysis.py

import pandas as pd
from textblob import TextBlob
import nltk
import re

# Télécharger les ressources nécessaires (à exécuter une fois)
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

from nltk.sentiment.vader import SentimentIntensityAnalyzer

def clean_text(text):
    """Nettoie le texte pour l'analyse de sentiment"""
    if not isinstance(text, str):
        return ""
    # Supprimer les URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Supprimer les caractères spéciaux et chiffres
    text = re.sub(r'[^\w\s]', '', text)
    return text

def analyze_sentiment_textblob(text):
    """Analyse le sentiment avec TextBlob"""
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return {'polarity': 0, 'subjectivity': 0}
    
    analysis = TextBlob(cleaned_text)
    return {
        'polarity': analysis.sentiment.polarity,  # -1 à 1 (négatif à positif)
        'subjectivity': analysis.sentiment.subjectivity  # 0 à 1 (objectif à subjectif)
    }

def analyze_sentiment_vader(text):
    """Analyse le sentiment avec VADER (plus adapté aux médias sociaux)"""
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return {'compound': 0, 'neg': 0, 'neu': 0, 'pos': 0}
    
    sid = SentimentIntensityAnalyzer()
    return sid.polarity_scores(cleaned_text)

def add_sentiment_analysis(df):
    """Ajoute l'analyse de sentiment au DataFrame"""
    if df.empty:
        return df
    
    # Créer une colonne combinant titre et texte pour l'analyse
    df['combined_text'] = df['title'].fillna('') + ' ' + df['selftext'].fillna('')
    
    # Appliquer l'analyse VADER (plus adaptée aux médias sociaux)
    sentiment_results = df['combined_text'].apply(analyze_sentiment_vader)
    
    # Extraire les scores dans des colonnes séparées
    df['sentiment_compound'] = sentiment_results.apply(lambda x: x['compound'])
    df['sentiment_negative'] = sentiment_results.apply(lambda x: x['neg'])
    df['sentiment_neutral'] = sentiment_results.apply(lambda x: x['neu'])
    df['sentiment_positive'] = sentiment_results.apply(lambda x: x['pos'])
    
    # Ajouter une catégorie de sentiment pour faciliter le filtrage
    df['sentiment_category'] = df['sentiment_compound'].apply(
        lambda score: 'Positif' if score >= 0.05 else 
                     ('Négatif' if score <= -0.05 else 'Neutre')
    )
    
    # Supprimer la colonne temporaire
    df.drop('combined_text', axis=1, inplace=True)
    
    return df

