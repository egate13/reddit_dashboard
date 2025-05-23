import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def train_predictive_model(df):
    """
    Entraîne un modèle de régression linéaire pour prédire les tendances futures.

    Parameters:
    - df (pd.DataFrame): DataFrame contenant les données Reddit.

    Returns:
    - model: Modèle entraîné.
    """
    # Exemple simplifié : prédire le score moyen des posts en fonction du nombre de commentaires
    X = df[['num_comments']]
    y = df['score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Évaluer le modèle
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print(f"Mean Squared Error: {mse}")

    return model

def predict_future_trends(model, new_data):
    """
    Utilise le modèle entraîné pour faire des prédictions sur de nouvelles données.

    Parameters:
    - model: Modèle entraîné.
    - new_data (pd.DataFrame): DataFrame contenant les nouvelles données pour la prédiction.

    Returns:
    - predictions: Prédictions du modèle.
    """
    predictions = model.predict(new_data)
    return predictions

