# Code_API/decision.py

def decision(proba, seuil=0.1):
    if proba < seuil:
        return "accepté"
    else:
        return "refusé"