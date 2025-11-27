import sys
import os

# Ajouter le dossier parent (Code_API) au PATH pour que 'import decision' fonctionne
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decision import decision  # import local à Code_API

def test_decision_acceptee():
    assert decision(0.05) == "accepté"

def test_decision_refusee():
    assert decision(0.2) == "refusé"