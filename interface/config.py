"""
config.py — Constantes de l'interface DocuClassif AI (partie B1, Jour 6).

Les libellés de catégories doivent rester identiques à ceux de l'API
(src/api/main.py, CATEGORIES) : c'est la clé de tous les filtres. Un test
de tests/test_ui_b1.py vérifie cette correspondance.
"""

APP_NAME = "DocuClassif AI"
APP_TAGLINE = (
    "Classification intelligente et assistant questions-réponses "
    "pour vos documents institutionnels"
)
APP_VERSION = "v1.0 · Jour 6"

# Adresse de l'API FastAPI, vue depuis le serveur Streamlit (jamais depuis le navigateur).
# Surchargeable avec la variable d'environnement DOCUCLASSIF_API_URL.
DEFAULT_API_URL = "http://127.0.0.1:8000"

# Les 5 catégories officielles, dans l'ordre de l'API, avec une description courte.
CATEGORIES = [
    {"label": "Règlements", "desc": "Lois, décrets, statuts"},
    {"label": "Guides pratiques", "desc": "Manuels, tutoriels, FAQ"},
    {"label": "Procédures", "desc": "Étapes, démarches"},
    {"label": "Organisation & plannings", "desc": "Calendriers, plannings"},
    {"label": "Formulaires & documents ponctuels", "desc": "Attestations, demandes"},
]
CATEGORY_LABELS = [c["label"] for c in CATEGORIES]

# Seuils de confiance de la page Upload (score entre 0 et 1).
SEUIL_CONFIANCE_HAUTE = 0.80   # strictement au-dessus : catégorie proposée à confirmer
SEUIL_CONFIANCE_MOYENNE = 0.60  # entre 0.60 et 0.80 : alternatives avec probabilités

# Texte d'exemple pour le bouton « Charger un exemple » (extrait réel du corpus).
EXEMPLE_TEXTE = (
    "GUIDE DES BOURSES ET AIDES FINANCIÈRES\n\n"
    "Campagne d'attribution des bourses - Année académique 2026-2027\n\n"
    "1. À propos de ce guide\n\n"
    "Ce guide présente l'ensemble des dispositifs d'aide financière proposés par "
    "l'Université de la Vakinankaratra à ses étudiants. Il précise les critères "
    "d'éligibilité, les montants, le calendrier de la campagne 2026-2027, les pièces "
    "à fournir et les voies de recours.\n\n"
    "À retenir : la campagne de dépôt des demandes court du 15 octobre au 30 novembre 2026."
)
