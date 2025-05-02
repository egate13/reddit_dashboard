```markdown
# Tableau de bord des tendances Reddit

Ce projet consiste à créer un tableau de bord interactif pour visualiser les tendances des publications Reddit, en se concentrant sur le subreddit r/popular. Il récupère les meilleures publications, les analyse et présente les informations à l'aide de graphiques et de tableaux interactifs.

## Fonctionnalités

* Récupère les 100 meilleures publications du subreddit r/popular.
* Enregistre les données récupérées dans un fichier CSV avec un horodatage.
* Visualise les tendances à l'aide de graphiques interactifs :
    * Top 20 des publications par score.
    * Top 20 des subreddits les plus fréquents dans le flux r/popular.
* Affiche les données brutes dans un tableau interactif avec des options de tri, de filtrage et de pagination.
* Mise à jour automatique du tableau de bord avec les données les plus récentes.

## Installation

1. Clonez le référentiel :

```bash
git clone https://github.com/votre_nom_utilisateur/reddit_dashboard.git
```

2. Créez un environnement virtuel :

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Installez les dépendances :

```bash
pip install -r requirements.txt
```

4. Configurez les informations d'identification de l'API Reddit :

* Créez une application de script sur Reddit : [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
* Remplacez les espaces réservés `CLIENT_ID`, `CLIENT_SECRET` et `USER_AGENT` dans `scrape_reddit_trends.py` par vos informations d'identification.

5. Exécutez le script de récupération :

```bash
python scrape_reddit_trends.py
```

6. Exécutez l'application de tableau de bord :

```bash
python main.py
```

7. Accédez au tableau de bord dans votre navigateur Web à l'adresse : `http://0.0.0.0:8050/`


## Utilisation

Le tableau de bord est mis à jour automatiquement avec les données les plus récentes. Vous pouvez interagir avec les graphiques et le tableau pour explorer les tendances.

## Améliorations futures

* Intégration de la base de données pour le stockage et la récupération des données.
* Options de personnalisation plus avancées pour le tableau de bord.
* Prise en charge de subreddits supplémentaires.
* Analyse des sentiments et du traitement du langage naturel.


## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des problèmes ou à soumettre des demandes d'extraction.

## Licence

Ce projet est sous licence MIT.
```
