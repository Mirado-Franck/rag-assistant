"""
data_mock.py — Données simulées pour la maquette (Jour 3, partie B1).

Aucune dépendance au backend (FastAPI), au classifieur (A1) ni à ChromaDB (A2).
Objectif : permettre de valider 100 % de l'interface seule.

Jour 4+ : remplacer les fonctions `predict_category` / `answer_question`
par les appels à l'API (`requests.post("http://localhost:8000/classify", ...)`).
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

APP_NAME = "DocuClassif AI"
APP_TAGLINE = "Classification intelligente et assistant questions-réponses pour vos documents institutionnels"
APP_VERSION = "v0.3 — Maquette Jour 3"

# ---------------------------------------------------------------------------
# Catégories institutionnelles (5)
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"key": "reglements", "label": "Règlements", "desc": "Lois, décrets, statuts", "count": 82},
    {"key": "guides", "label": "Guides pratiques", "desc": "Manuels, tutoriels, FAQ", "count": 45},
    {"key": "procedures", "label": "Procédures", "desc": "Étapes, workflows", "count": 67},
    {"key": "organisation", "label": "Organisation", "desc": "Plannings, organigrammes", "count": 38},
    {"key": "formulaires", "label": "Formulaires", "desc": "Attestations, demandes", "count": 49},
]
CATEGORY_LABELS = [c["label"] for c in CATEGORIES]
CATEGORY_BY_LABEL = {c["label"]: c for c in CATEGORIES}

# ---------------------------------------------------------------------------
# Statistiques globales (simulées)
# ---------------------------------------------------------------------------
STATS = {
    "documents": 15,
    "chunks": 281,
    "questions": 47,
    "classifications": 12,
    "documents_delta": 3,
    "confirmation_rate": 100,
    "avg_confidence": 91,
    "avg_latency": "3.2 s",
}

TOTAL_CHUNKS = sum(c["count"] for c in CATEGORIES)  # 281 -> cohérent avec STATS

# ---------------------------------------------------------------------------
# Documents (simulés)
# ---------------------------------------------------------------------------
_DOCS_RAW = [
    ("01_reglement_interieur.pdf", "Règlements", 0.97, 34, 2),
    ("02_guide_bourses.docx", "Guides pratiques", 0.93, 22, 5),
    ("03_procedure_inscription.pdf", "Procédures", 0.88, 19, 8),
    ("04_calendrier_academique.pdf", "Organisation", 0.95, 11, 12),
    ("05_formulaire_demande_stage.docx", "Formulaires", 0.91, 8, 15),
    ("06_statut_du_personnel.pdf", "Règlements", 0.89, 27, 21),
    ("07_guide_utilisateur_intranet.pdf", "Guides pratiques", 0.84, 16, 26),
    ("08_procedure_achat.pdf", "Procédures", 0.86, 24, 33),
]

DOCUMENTS = [
    {
        "fichier": name,
        "categorie": cat,
        "confiance": conf,
        "chunks": chunks,
        "date": (date.today() - timedelta(days=days_ago)).isoformat(),
        "statut": "Confirmé",
    }
    for name, cat, conf, chunks, days_ago in _DOCS_RAW
]

DOCUMENT_NAMES = [d["fichier"] for d in DOCUMENTS]

# ---------------------------------------------------------------------------
# Classifications récentes (page Upload / Dashboard)
# ---------------------------------------------------------------------------
RECENT_CLASSIFICATIONS = [
    {"Fichier": "01_reglement_interieur.pdf", "Catégorie": "Règlements", "Confiance": "97 %", "Statut": "Confirmé"},
    {"Fichier": "02_guide_bourses.docx", "Catégorie": "Guides pratiques", "Confiance": "93 %", "Statut": "Confirmé"},
    {"Fichier": "06_statut_du_personnel.pdf", "Catégorie": "Règlements", "Confiance": "89 %", "Statut": "Confirmé"},
    {"Fichier": "08_procedure_achat.pdf", "Catégorie": "Procédures", "Confiance": "86 %", "Statut": "En attente"},
]

# ---------------------------------------------------------------------------
# Journal de discussion initial (page Questions)
# ---------------------------------------------------------------------------
INITIAL_CHAT = [
    {
        "role": "assistant",
        "content": (
            "Je réponds à vos questions **uniquement à partir des documents de la base**. "
            "Utilisez les filtres ci-dessus pour restreindre la recherche à une catégorie "
            "ou à un fichier précis. Les réponses citent toujours leurs sources."
        ),
        "sources": [],
        "meta": {},
    }
]

# ---------------------------------------------------------------------------
# Classifieur factice (Jour 3)
# ---------------------------------------------------------------------------
_KEYWORDS = {
    "Règlements": ["règlement", "reglement", "statut", "décret", "decret", "loi", "article", "sanction", "discipline"],
    "Guides pratiques": ["guide", "manuel", "tutoriel", "faq", "comment", "aide", "mode d'emploi"],
    "Procédures": ["procédure", "procedure", "étape", "etape", "circuit", "workflow", "instruction", "traitement"],
    "Organisation": ["calendrier", "planning", "organigramme", "réunion", "reunion", "service", "année", "annee"],
    "Formulaires": ["formulaire", "demande", "attestation", "cerfa", "modèle", "modele", "engagement"],
}


def _seed(text: str) -> float:
    """Hash stable -> valeur pseudo-aléatoire déterministe entre 0 et 1."""
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def predict_category(filename: str, text: str = "") -> dict:
    """
    Classification simulée : renvoie la catégorie, le score de confiance
    et les 3 alternatives (comme le fera le classifieur zero-shot de A1).
    """
    haystack = f"{filename} {text}".lower()
    scores = {}
    for label, words in _KEYWORDS.items():
        scores[label] = sum(haystack.count(w) for w in words)

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:  # aucun mot-clé : choix stable dérivé du nom de fichier
        best = CATEGORY_LABELS[int(_seed(filename) * len(CATEGORY_LABELS)) % len(CATEGORY_LABELS)]

    confidence = 0.62 + _seed(filename + best) * 0.34  # entre 62 % et 96 %
    others = sorted((l for l in CATEGORY_LABELS if l != best), key=lambda l: -scores.get(l, 0))
    alternatives = [
        {"label": label, "score": round(max(0.02, (1 - confidence) * f), 2)}
        for label, f in zip(others[:3], (1.0, 0.6, 0.35))
    ]
    return {
        "categorie": best,
        "confiance": round(confidence, 3),
        "alternatives": alternatives,
        "chunks_estimes": 6 + int(_seed(best + filename) * 28),
        "fiable": confidence >= 0.75,
    }


# ---------------------------------------------------------------------------
# RAG factice (Jour 3)
# ---------------------------------------------------------------------------
_ANSWERS = {
    "bourse": (
        "D'après les documents disponibles, les conditions d'obtention d'une bourse sont :\n"
        "1. être inscrit en formation initiale ;\n"
        "2. avoir une moyenne générale supérieure à 12/20 ;\n"
        "3. déposer un dossier complet (CIN, relevé de notes, certificat de scolarité, "
        "attestation de revenus) avant le **30 octobre**."
    ),
    "inscription": (
        "L'inscription se fait en 4 étapes : retrait du dossier auprès du service de "
        "scolarité, dépôt des pièces justificatives, validation par la commission "
        "pédagogique, puis édition de la carte d'étudiant sous 5 jours ouvrés."
    ),
    "stage": (
        "Toute demande de stage doit être accompagnée du formulaire de demande, de "
        "l'attestation de l'établissement d'accueil et de l'engagement de confidentialité "
        "signé par l'encadrant."
    ),
}

_DEFAULT_ANSWER = (
    "Voici ce que j'ai trouvé dans les documents correspondant à votre question. "
    "La réponse est reconstruite à partir des extraits les plus pertinents de votre base "
    "documentaire ; ouvrez les sources ci-dessous pour vérifier chaque élément."
)

_SOURCES = [
    {"fichier": "02_guide_bourses.docx", "categorie": "Guides pratiques", "ref": "Page 3, §2", "score": 0.92},
    {"fichier": "01_reglement_interieur.pdf", "categorie": "Règlements", "ref": "Article 45", "score": 0.87},
    {"fichier": "03_procedure_inscription.pdf", "categorie": "Procédures", "ref": "Étape 4", "score": 0.81},
    {"fichier": "04_calendrier_academique.pdf", "categorie": "Organisation", "ref": "Semestre 1", "score": 0.74},
    {"fichier": "05_formulaire_demande_stage.docx", "categorie": "Formulaires", "ref": "Rubrique B", "score": 0.69},
]


def answer_question(question: str, scope: str = "Tous", n_sources: int = 3) -> dict:
    """Réponse RAG simulée + sources filtrées selon la portée choisie."""
    q = question.lower()
    answer = next((v for k, v in _ANSWERS.items() if k in q), _DEFAULT_ANSWER)

    sources = [s for s in _SOURCES if s["score"] > 0]
    if scope not in ("Tous", "Tous les documents"):
        sources = [s for s in sources if s["categorie"] == scope] or sources
    sources = sources[:n_sources]

    return {
        "content": answer,
        "sources": sources,
        "meta": {
            "latence": f"{1.4 + _seed(question) * 2.6:.1f} s",
            "pertinence": f"{68 + int(_seed(question) * 28)} %",
            "filtre": scope,
        },
    }
