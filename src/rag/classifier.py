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

# Descriptions détaillées pour aider le LLM à distinguer
CATEGORY_DESCRIPTIONS = {
    "Règlements": (
        "Textes normatifs et contraignants : lois, décrets, arrêtés, "
        "règlements intérieurs, codes, articles de loi, statuts. "
        "Contient souvent des articles numérotés, des obligations, "
        "des interdictions, des sanctions."
    ),
    "Guides pratiques": (
        "Manuels, tutoriels, instructions, conseils, FAQ, guides "
        "d'utilisation, bonnes pratiques. Explique COMMENT faire "
        "quelque chose de manière pédagogique."
    ),
    "Procédures": (
        "Étapes à suivre, processus, workflows, démarches "
        "administratives, protocoles. Décrit une séquence d'actions "
        "dans un ordre précis (étape 1, étape 2, etc.)."
    ),
    "Organisation & plannings": (
        "Organigrammes, calendriers, emplois du temps, structures "
        "organisationnelles, répartition des rôles, planning "
        "d'activités, tableaux de bord organisationnels."
    ),
    "Formulaires & documents ponctuels": (
        "Formulaires à remplir, attestations, certificats, lettres "
        "types, demandes, déclarations, bordereaux, fiches de "
        "renseignements. Documents destinés à être complétés."
    )
}

PROMPT_TEMPLATE = """Tu es un classifieur de documents institutionnels. 
Ta tâche est d'analyser le texte suivant et de le classer dans EXACTEMENT UNE 
des 5 catégories ci-dessous.

CATÉGORIES DISPONIBLES :
1. Règlements : {desc_reglements}
2. Guides pratiques : {desc_guides}
3. Procédures : {desc_procedures}
4. Organisation & plannings : {desc_org}
5. Formulaires & documents ponctuels : {desc_form}

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
---"""

def classify_document(text, model_name="llama3.2"):
    """
    Classifie un document dans une des 5 catégories.
    
    Args:
        text: Le texte complet du document
        model_name: Le nom du modèle Ollama à utiliser
    
    Returns:
        dict: {"categorie": str, "confiance": float, "justification": str}
    """
    llm = ChatOllama(model=model_name, temperature=0.1)
    
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
    llm = ChatOllama(model=model_name, temperature=0.1)
    text_truncated = text[:2000] if len(text) > 2000 else text
    
    alt_prompt = f"""Le texte suivant est ambigu. Classe-le dans les 5 catégories 
par ordre de probabilité décroissante.

Catégories : {', '.join(CATEGORIES)}

Réponds UNIQUEMENT en JSON :
{{"classement": [
    {{"categorie": "...", "probabilite": 0.65}},
    {{"categorie": "...", "probabilite": 0.20}},
    {{"categorie": "...", "probabilite": 0.10}}
]}}

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
        ("Extrait règlement", "Article 12 : Tout étudiant inscrit en première année "
         "de licence doit s'acquitter des frais d'inscription avant le 30 septembre. "
         "Tout retard entraînera une pénalité de 10% par semaine de retard. "
         "Article 13 : L'exclusion définitive sera prononcée en cas de fraude "
         "lors des examens."),
        
        ("Extrait guide", "Pour bien préparer votre rentrée universitaire, "
         "voici quelques conseils pratiques. Commencez par vérifier votre "
         "emploi du temps sur le portail étudiant. Ensuite, rendez-vous à la "
         "bibliothèque pour activer votre carte de prêt. N'oubliez pas de "
         "télécharger l'application mobile de l'université."),
        
        ("Extrait procédure", "Étape 1 : Déposez votre dossier de demande de "
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
        print(f"   Justification : {result['justification']}")
        print()