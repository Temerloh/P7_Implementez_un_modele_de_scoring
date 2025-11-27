from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from contextlib import asynccontextmanager
import os 
import joblib # Import de joblib pour le chargement direct du modèle

# Constantes de l'application
SEUIL_METIER = 0.10
# Assurez-vous que ces fichiers sont dans le même répertoire que api.py lors de l'exécution
LOCAL_MODEL_PATH = "model.pkl" 
DATA_PATH_DEPLOY = "donnees_prepared_10percent.csv"

# Variables globales pour le modèle et les données
model = None
data_prepared = None
client_ids = [] 

class ClientID(BaseModel):
    SK_ID_CURR: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Fonction de démarrage de l'application (lifespan).
    Charge le dataset et le modèle localement au lancement.
    Ceci se produit une seule fois lors du démarrage de l'API.
    """
    global model, data_prepared, client_ids

    # --- 1. Chargement du Dataset ---
    try:
        print(f"INFO: Chargement du dataset depuis {DATA_PATH_DEPLOY}")
        data_prepared = pd.read_csv(DATA_PATH_DEPLOY)
        client_ids = data_prepared['SK_ID_CURR'].unique().tolist()
    except FileNotFoundError:
        current_dir = os.getcwd()
        raise RuntimeError(f"Fichier de données non trouvé : '{DATA_PATH_DEPLOY}'. "
                           f"Vérifiez qu'il est dans le répertoire d'exécution : {current_dir}")

    # --- 2. Chargement du Modèle LOCAL ---
    try:
        print(f"INFO: Tentative de chargement du modèle local depuis : {LOCAL_MODEL_PATH}")
        model = joblib.load(LOCAL_MODEL_PATH)
        print("INFO: Modèle chargé avec succès (localement). API prête.")
        
    except FileNotFoundError:
        current_dir = os.getcwd()
        raise RuntimeError(f"Fichier modèle non trouvé : '{LOCAL_MODEL_PATH}'. "
                           f"Vérifiez qu'il est dans le répertoire d'exécution : {current_dir}")
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement du modèle local. Erreur détaillée: {e}")
    
    yield
    
app = FastAPI(lifespan=lifespan)

# --- ENDPOINT: Retourne la liste des ID clients ---
@app.get("/clients")
def get_clients():
    """Returns the list of all client IDs (SK_ID_CURR) available in the dataset."""
    if not client_ids:
        raise HTTPException(status_code=500, detail="La liste des clients n'est pas disponible. Vérifiez le chargement des données.")
    return client_ids

@app.post("/predict")
def predict(client: ClientID):
    """Point d'accès pour obtenir la prédiction de défaut de paiement pour un client."""
    if model is None or data_prepared is None:
        raise HTTPException(status_code=500, detail="Ressources (Modèle/Données) non chargées.")

    row = data_prepared.loc[data_prepared['SK_ID_CURR'] == client.SK_ID_CURR]

    if row.empty:
        # Renvoie 404 client non trouvé
        raise HTTPException(status_code=404, detail=f"Client {client.SK_ID_CURR} non trouvé dans les données")

    # Retirer la colonne SK_ID_CURR pour la prédiction
    features = row.drop(columns=['SK_ID_CURR']).values

    # Prédiction de la probabilité
    # [:, 1] sélectionne la probabilité de la classe positive (défaut)
    proba_defaut = model.predict_proba(features)[:, 1][0]
    
    # Décision métier basée sur le seuil
    decision = "refusé" if proba_defaut >= SEUIL_METIER else "accepté"

    return {
        "client_id": client.SK_ID_CURR,
        "probabilité_defaut": float(proba_defaut),
        "décision": decision
    }