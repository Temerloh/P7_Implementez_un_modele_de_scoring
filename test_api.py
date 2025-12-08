import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import api  # votre module api.py

@pytest.fixture(scope="module")
def client():
    # Simulation des données factices pour le CSV
    fake_data = pd.DataFrame({
        'SK_ID_CURR': [123],
        'feature1': [0.5],
        'feature2': [1.5]
    })

    # Modèle factice simulant la méthode predict_proba
    fake_model = MagicMock()
    fake_model.predict_proba.return_value = np.array([[0.3, 0.7]])  # probas pour 2 classes

    # Patcher pd.read_csv ET joblib.load DANS le module api (c'est important)
    with patch('api.pd.read_csv', return_value=fake_data), \
         patch('api.joblib.load', return_value=fake_model):

        # Création du TestClient déclenche lifespan avec mocks appliqués
        with TestClient(api.app) as test_client:
            yield test_client

def test_get_clients(client):
    response = client.get("/clients")
    assert response.status_code == 200
    assert 123 in response.json()

def test_predict_accept(client):
    response = client.post("/predict", json={"SK_ID_CURR": 123})
    assert response.status_code == 200
    data = response.json()
    assert data['client_id'] == 123
    assert data['décision'] == "refusé"  # car 0.7 > SEUIL_METIER (0.10)

def test_predict_no_client(client):
    response = client.post("/predict", json={"SK_ID_CURR": 999})
    assert response.status_code == 404