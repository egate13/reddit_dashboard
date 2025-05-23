# Reddit Trends Dashboard

## Description

Le Reddit Trends Dashboard est une application web interactive basée sur Dash et Flask, conçue pour visualiser et analyser les tendances et discussions sur Reddit. Cette application permet de charger des données Reddit, de les filtrer, et de les visualiser sous différentes formes, y compris des graphiques et des tableaux de données.

## Fonctionnalités

- **Chargement et filtrage des données** : Charger des données Reddit à partir de fichiers CSV et filtrer par subreddit.
- **Analyse de sentiment** : Analyser le sentiment des posts Reddit et visualiser la distribution du sentiment, le sentiment par subreddit, et l'évolution du sentiment dans le temps.
- **Détection de tendances émergentes** : Identifier les sujets en croissance rapide avant qu'ils ne deviennent viraux.
- **Comparaison concurrentielle** : Comparer les mentions de différentes marques/produits concurrents avec des métriques d'engagement.
- **Segmentation par audience** : Analyser les profils des utilisateurs qui interagissent avec certains contenus pour mieux comprendre les segments d'audience.

## Installation

### Prérequis

- Python 3.7+
- Virtualenv (recommandé)

### Étapes d'installation

1. **Cloner le dépôt**

    ```bash
    git clone https://github.com/votre-utilisateur/reddit-dashboard.git
    cd reddit-dashboard
    ```

2. **Créer et activer un environnement virtuel**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
    ```

3. **Installer les dépendances**

    ```bash
    pip install -r requirements.txt
    ```

4. **Télécharger les ressources NLTK**

    ```bash
    python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('vader_lexicon')"
    ```

## Utilisation

1. **Lancer l'application**

    ```bash
    python main.py
    ```

2. **Accéder à l'application**

    Ouvrez votre navigateur et allez à `http://127.0.0.1:8050/`.

## Structure du projet


