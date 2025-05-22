# Utilisez une image de base Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de l'application
COPY . /app

# Installer les dépendances
RUN pip install --no-cache-dir -r src/requirements.txt

# Exposer le port sur lequel l'application s'exécute
EXPOSE 8050

# Commande pour démarrer l'application
CMD ["python", "src/main.py"]

