import json
import re
from langchain_ollama import ChatOllama

# Les 5 catégories officielles
CATEGORIES = [
    "Règlements",
    "Guides pratiques",
    "Procédures",
    "Organisation & plannings",
    "Formulaires & documents ponctuels"
]

# Descriptions détaillées V4 - optimisées pour 08 et 09
CATEGORY_DESCRIPTIONS = {
    "Règlements": (
        "Textes normatifs obligatoires et sanctionnés : lois, décrets, arrêtés, "
        "règlements intérieurs, articles de loi, statuts. "
        "Contient 'Article X', 'interdit', 'obligatoire', 'sanction', 'exclusion', 'pénalité'. "
        "Ton d'autorité et d'interdiction."
    ),
    "Guides pratiques": (
        "Document PÉDAGOGIQUE qui explique le POURQUOI et le CONTEXTE (crédits, objectifs, modalités) "
        "puis donne des conseils pratiques. Ton d'accompagnement et bienveillant ('conseils', 'astuces', "
        "'recommandations', 'FAQ', 'comment bien faire'). "
        "Même s'il donne quelques étapes, son but principal est d'expliquer et d'orienter, pas d'imposer une démarche administrative stricte."
    ),
    "Procédures": (
        "Démarche administrative stricte et OBLIGATOIRE pour obtenir quelque chose. "
        "Verbes à l'impératif + ordre impératif et délais contraignants. "
        "Contient 'Étape 1', 'Étape 2', 'dossier à déposer', 'joindre', 'au moins 15 jours avant', 'obligatoirement', 'sous peine de refus'. "
        "Si tu rates une étape, ta demande est REFUSÉE."
    ),
    "Organisation & plannings": (
        "CALENDRIER / PLANNING / TABLEAU DE DATES qui INFORME (pas qui ordonne). "
        "Signaux forts : 'CALENDRIER ACADÉMIQUE', 'Arrêté n°', 'Période', 'Dates', 'Rentrée', 'Semestre', 'Examens', 'Vacances', 'Jurys', 'Année académique'. "
        "Il liste QUAND se passe QUOI dans un tableau Période/Dates/Événement. "
        "Il ne dit PAS 'Étape 1 déposez, Étape 2 attendez'. Lister des dates ou mentionner 'Inscriptions 5-31 octobre' ne suffit PAS à en faire une procédure."
    ),
    "Formulaires & documents ponctuels": (
        "Modèle à remplir avec cases vides : formulaire, attestation, certificat, convention, demande type. "
        "Contient 'Nom : ...', 'Signature : ...', 'Date : ...', champs à compléter. "
        "Document destiné à être complété et rendu."
    )
}

PROMPT_TEMPLATE = """Tu es un classifieur de documents institutionnels.

Ta tâche est d'analyser le texte suivant et de le classer dans EXACTEMENT UNE des 5 catégories ci-dessous.

CATÉGORIES DISPONIBLES :

1. Règlements :
{desc_reglements}

2. Guides pratiques :
{desc_guides}

3. Procédures :
{desc_procedures}

4. Organisation & plannings :
{desc_org}

5. Formulaires & documents ponctuels :
{desc_form}

RÈGLES DE DÉPARTAGE (TRÈS IMPORTANT) :
- Si le document est un CALENDRIER avec tableau Période/Dates/Événement = Organisation & plannings, JAMAIS Procédures (même s'il liste des inscriptions ou campagnes).
- Procédures = seulement si le texte détaille COMMENT faire une démarche étape par étape avec verbes d'action obligatoires ('remplir', 'déposer', 'joindre'). Lister des dates ne suffit PAS.
- Guide qui explique le contexte (crédits, objectifs, modalités) + donne des étapes = Guides pratiques, pas Procédures (sauf si le titre est 'Procédure de...').
- Ne classe en "Procédures" QUE si le texte décrit une démarche administrative avec des étapes numérotées et obligatoires. Un simple guide avec des conseils n'est PAS une procédure.

INSTRUCTIONS :
- Analyse le contenu, le ton, la structure et le vocabulaire du texte.
- Choisis la catégorie la PLUS pertinente.
- Donne un score de confiance entre 0.0 et 1.0.
- Si le texte est très court ou ambigu, donne un score bas (< 0.6).
- Réponds UNIQUEMENT au format JSON, sans aucun autre texte.

FORMAT DE RÉPONSE OBLIGATOIRE :
{{"categorie": "nom exact de la catégorie", "confiance": 0.85, "justification": "une phrase expliquant le choix"}}

TEXTE À CLASSIFIER (premiers 2000 caractères) :
---
{texte}
---
"""

def classify_document(text, model_name="llama3.2"):
    """
    Classifie un document dans une des 5 catégories.

    Args:
        text: Le texte complet du document
        model_name: Le nom du modèle Ollama à utiliser

    Returns:
        dict: {"categorie": str, "confiance": float, "justification": str}
    """
    llm = ChatOllama(
        model=model_name,
        temperature=0.1,
        base_url="http://127.0.0.1:11434",
        timeout=60
    )

    # Tronquer le texte pour ne pas dépasser la fenêtre de contexte
    text_truncated = text[:2000] if len(text) > 2000 else text

    prompt = PROMPT_TEMPLATE.format(
        desc_reglements=CATEGORY_DESCRIPTIONS["Règlements"],
        desc_guides=CATEGORY_DESCRIPTIONS["Guides pratiques"],
        desc_procedures=CATEGORY_DESCRIPTIONS["Procédures"],
        desc_org=CATEGORY_DESCRIPTIONS["Organisation & plannings"],
        desc_form=CATEGORY_DESCRIPTIONS["Formulaires & documents ponctuels"],
        texte=text_truncated
    )

    response = llm.invoke(prompt)
    raw = response.content.strip()

    # Extraire le JSON de la réponse (le LLM peut ajouter du texte autour)
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not json_match:
        return {
            "categorie": "Inconnu",
            "confiance": 0.0,
            "justification": f"Impossible de parser la réponse : {raw[:100]}"
        }

    try:
        result = json.loads(json_match.group())

        # Vérifier que la catégorie est valide
        if result.get("categorie") not in CATEGORIES:
            # Essayer de trouver la catégorie la plus proche
            for cat in CATEGORIES:
                if cat.lower() in result["categorie"].lower():
                    result["categorie"] = cat
                    break
            else:
                result["categorie"] = "Inconnu"
                result["confiance"] = 0.0

        return result

    except json.JSONDecodeError:
        return {
            "categorie": "Inconnu",
            "confiance": 0.0,
            "justification": f"JSON invalide : {raw[:100]}"
        }


def classify_with_alternatives(text, model_name="llama3.2"):
    """
    Classifie un document et retourne aussi les alternatives possibles.
    Utile quand la confiance est basse.
    """
    # Première classification
    primary = classify_document(text, model_name)

    # Si confiance haute, pas besoin d'alternatives
    if primary["confiance"] >= 0.8:
        return {
            "primary": primary,
            "alternatives": [],
            "needs_confirmation": False
        }

    # Si confiance basse, demander les alternatives
    llm = ChatOllama(
        model=model_name,
        temperature=0.1,
        base_url="http://127.0.0.1:11434",
        timeout=60
    )
    text_truncated = text[:2000] if len(text) > 2000 else text

    alt_prompt = f"""Le texte suivant est ambigu. Classe-le dans les 5 catégories 
par ordre de probabilité décroissante.

Catégories : {', '.join(CATEGORIES)}

Réponds UNIQUEMENT en JSON :
{{"classement": [{{"categorie": "...", "probabilite": 0.65}}, {{"categorie": "...", "probabilite": 0.20}}, {{"categorie": "...", "probabilite": 0.10}}]}}

Texte :
---
{text_truncated}
---"""

    response = llm.invoke(alt_prompt)
    raw = response.content.strip()
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)

    alternatives = []
    if json_match:
        try:
            alt_result = json.loads(json_match.group())
            alternatives = alt_result.get("classement", [])[:3]
        except json.JSONDecodeError:
            pass

    return {
        "primary": primary,
        "alternatives": alternatives,
        "needs_confirmation": True
    }


# === TEST RAPIDE ===
if __name__ == "__main__":
    print("🧪 Test du classifieur zero-shot\n")

    # Tester avec un extrait de chaque type
    test_texts = [
        ("Extrait règlement", 
         "Article 12 : Tout étudiant inscrit en première année "
         "de licence doit s'acquitter des frais d'inscription avant le 30 septembre. "
         "Tout retard entraînera une pénalité de 10% par semaine de retard. "
         "Article 13 : L'exclusion définitive sera prononcée en cas de fraude "
         "lors des examens."),
        
        ("Extrait guide", 
         "Pour bien préparer votre rentrée universitaire, "
         "voici quelques conseils pratiques. Commencez par vérifier votre "
         "emploi du temps sur le portail étudiant. Ensuite, rendez-vous à la "
         "bibliothèque pour activer votre carte de prêt. N'oubliez pas de "
         "télécharger l'application mobile de l'université."),
        
        ("Extrait procédure", 
         "Étape 1 : Déposez votre dossier de demande de "
         "bourse au bureau de la scolarité. Étape 2 : Attendez la confirmation "
         "de réception par email (délai : 48h). Étape 3 : Présentez-vous à "
         "l'entretien avec le comité de sélection muni de votre CIN et de "
         "votre relevé de notes. Étape 4 : La décision sera communiquée "
         "sous 15 jours ouvrables."),
    ]

    for name, text in test_texts:
        print(f"📄 {name} :")
        result = classify_document(text)
        print(f"   Catégorie : {result['categorie']}")
        print(f"   Confiance : {result['confiance']:.0%}")
        print(f"   Justification : {result['justification']}\n")
