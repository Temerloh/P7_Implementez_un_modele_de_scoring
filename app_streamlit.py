# IMPORTANT: This application requires the 'streamlit' and 'requests' libraries.
# Install them with: pip install streamlit requests
import streamlit as st
import requests
import json

# --- Configuration de l'Application Streamlit ---
st.set_page_config(
    page_title="Analyse de Crédit Client - API FastAPI",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Constantes de l'API
API_BASE_URL = "http://localhost:8000"
API_PREDICT_URL = f"{API_BASE_URL}/predict"
API_CLIENTS_URL = f"{API_BASE_URL}/clients"

@st.cache_data
def fetch_client_ids():
    """Fetches the list of all available client IDs from the FastAPI API."""
    try:
        response = requests.get(API_CLIENTS_URL)
        if response.status_code == 200:
            return response.json()
        
        st.error(f"Erreur lors de la récupération des IDs clients (Code: {response.status_code}).")
        return []
    except requests.exceptions.ConnectionError:
        st.error(f"🔴 Erreur de Connexion: Impossible de joindre l'API à {API_CLIENTS_URL}.")
        st.warning("Vérifiez que votre serveur Uvicorn est bien démarré et écoute sur `http://localhost:8000`.")
        return []

def main():
    """Fonction principale de l'application Streamlit."""
    
    st.title("👨‍💻 Démonstrateur d'API de Scoring Crédit")
    st.subheader("Test de l'endpoint FastAPI `/predict`")
    
    st.markdown("""
        Sélectionnez l'identifiant client (SK_ID_CURR) pour obtenir la prédiction
        de défaut de paiement via l'API locale.
        
        ⚠️ **Rappel:** L'API doit être démarrée séparément (via `uvicorn api:app --reload`).
    """)

    # --- Récupération et Affichage de la Liste des IDs Clients ---
    available_ids = fetch_client_ids()
    
    if available_ids:
        client_id = st.selectbox(
            "Sélectionnez l'ID Client (SK_ID_CURR)",
            options=available_ids,
            help="Liste des IDs disponibles dans le jeu de données chargé par l'API."
        )
    else:
        st.warning("Aucun ID client récupéré. Assurez-vous que l'API est démarrée et que l'endpoint `/clients` est fonctionnel.")
        client_id = st.number_input(
            "Entrez l'ID Client (SK_ID_CURR) manuellement",
            min_value=100000,
            max_value=999999,
            value=100001,
            step=1
        )
    
    # --- Bouton de Prédiction ---
    if st.button("Obtenir la Prédiction"):
        
        # Affichage du spinner pendant l'appel API
        with st.spinner(f"Envoi de la requête pour l'ID {client_id} à l'API..."):
            
            # 1. Préparation des données JSON à envoyer
            payload = {"SK_ID_CURR": client_id}
            
            try:
                # 2. Appel à l'API FastAPI
                response = requests.post(API_PREDICT_URL, json=payload)
                
                # 3. Traitement de la réponse
                if response.status_code == 200:
                    data = response.json()
                    
                    st.success("✅ Prédiction Réussie !")
                    
                    proba = data.get("probabilité_defaut")
                    decision = data.get("décision")
                    
                    # Mise en forme de la décision
                    color = "red" if decision == "refusé" else "green"
                    
                    st.markdown(f"### Décision: <span style='color:{color}; font-size: 30px;'>{decision.upper()}</span>", unsafe_allow_html=True)
                    st.write(f"Probabilité de défaut: **{proba:.4f}**")
                    
                    # Affichage des données brutes pour le débogage
                    st.markdown("---")
                    st.json(data)

                elif response.status_code == 404:
                    # Gestion du cas où l'ID client n'est pas trouvé
                    error_data = response.json()
                    st.error(f"❌ Client Non Trouvé: {error_data.get('detail', 'ID client inconnu.')}")

                else:
                    # Gestion des autres erreurs HTTP (500, 400, etc.)
                    st.error(f"Erreur de l'API (Code: {response.status_code})")
                    st.json(response.json())

            except requests.exceptions.ConnectionError:
                st.error(f"🔴 Erreur de Connexion: Impossible de joindre l'API à {API_PREDICT_URL}.")
                st.warning("Vérifiez que votre serveur Uvicorn est bien démarré et écoute sur `http://localhost:8000`.")
            except json.JSONDecodeError:
                st.error("L'API a renvoyé une réponse invalide (non-JSON).")
            except Exception as e:
                st.error(f"Une erreur inattendue est survenue: {e}")

if __name__ == "__main__":
    main()