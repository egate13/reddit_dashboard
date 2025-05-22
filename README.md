# Reddit Dashboard

Ce projet propose un tableau de bord interactif pour visualiser les tendances du subreddit **r/popular** sur Reddit. Il comprend un scraper pour collecter les données via l’API Reddit, ainsi qu’une interface web (Dash/Flask) pour explorer et analyser ces tendances.

---

## Fonctionnalités principales

- **Scraping Reddit** : Récupère les posts les plus populaires de r/popular (ou tout autre subreddit défini).
- **Stockage des données** : Les données sont sauvegardées dans un bucket Supabase.
- **Dashboard interactif** :
  - Visualisation des top posts par score.
  - Statistiques sur les subreddits les plus fréquents.
  - Tableau filtrable et triable de toutes les données collectées.
- **Interface web** : Application Dash servie via Flask, accessible sur le port 8050.

---

## Structure du projet

```
src/
├── dashboard.py         # Code principal du dashboard Dash + callbacks
├── main.py              # Point d'entrée Flask, lance le serveur web
├── scrape_reddit.py     # Scraper Reddit, exporte les données CSV
├── requirements.txt     # Dépendances Python
├── __pycache__/         # Fichiers compilés Python (auto-générés)
├── venv/                # Environnement virtuel (optionnel, à ne pas versionner)
```

---

## Installation

### Cloner le dépôt

```bash
git clone https://github.com/egate13/reddit_dashboard.git
cd reddit_dashboard/src
```

### Créer un environnement virtuel (optionnel mais recommandé)

```bash
python3 -m venv venv
source venv/bin/activate
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

### Configurer les accès Reddit

Éditez `scrape_reddit.py` et remplacez les valeurs de `CLIENT_ID`, `CLIENT_SECRET` et `USER_AGENT` avec vos propres identifiants Reddit ([voir ici](https://www.reddit.com/prefs/apps)).

### Configurer Supabase

Assurez-vous d'avoir un compte Supabase et configurez les variables `SUPABASE_URL` et `SUPABASE_KEY` dans `scrape_reddit.py` et `dashboard.py` avec vos informations de connexion Supabase.

---

## Utilisation

### 1. Scraper les données Reddit

Lancez le script de scraping pour générer un fichier CSV et l'uploader vers Supabase :

```bash
python scrape_reddit.py
```

### 2. Lancer le dashboard

Démarrez le serveur Flask/Dash :

```bash
python main.py
```

Le dashboard sera accessible à l’adresse [http://localhost:8050](http://localhost:8050)

### 3. Explorer le dashboard

- **Top Posts by Score** : Diagramme des 20 posts les plus populaires.
- **Most Frequent Subreddits** : Classement des subreddits les plus présents dans le flux.
- **Raw Data** : Tableau interactif avec filtres, tris et recherche.

---

## Personnalisation

- Pour changer le subreddit scrappé, modifiez la variable `SUBREDDIT_NAME` dans `scrape_reddit.py`.
- Pour changer le nombre de posts collectés, ajustez la variable `POST_LIMIT`.

---

## Dépendances

- dash
- plotly
- pandas
- praw
- supabase

(voir `requirements.txt`)

---

## Notes

- Le répertoire `venv/` et `__pycache__/` ne doivent pas être versionnés (ajouter à `.gitignore`).
- Les identifiants Reddit et Supabase sont obligatoires pour le scraping et l'accès aux données.

---

## Exemples de fichiers générés

- `data/reddit_trends_20240516.csv` : Exemple de fichier de données collectées.

---

## Contributions

Les contributions sont les bienvenues ! Veuillez ouvrir une issue ou une pull request pour discuter des améliorations ou des corrections.

---

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
```

### Conclusion

Ce `README.md` mis à jour reflète les modifications apportées à votre projet, notamment l'utilisation de Supabase pour le stockage des données et l'intégration des scripts de scraping et de dashboard. Assurez-vous de personnaliser les sections de configuration et d'utilisation en fonction de vos besoins spécifiques.
