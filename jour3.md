# 🔄 PLAN RÉVISÉ — Classification + RAG (Option B)

---

## 📐 Architecture Technique Révisée

Avant de donner le Jour 3, voici la nouvelle architecture complète pour que tout le monde comprenne ce qu'on construit :

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE STREAMLIT                       │
│                                                             │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │ 📤 Upload │  │ 💬 Questions  │  │ 📊 Tableau de bord   │  │
│  │ + Classif │  │ + Filtres     │  │ (stats, catégories)  │  │
│  └─────┬─────┘  └──────┬────────┘  └──────────────────────┘  │
│        │               │                                     │
└────────┼───────────────┼─────────────────────────────────────┘
         │               │
         ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                     API FASTAPI                              │
│                                                             │
│  POST /api/upload      → Upload + Extraction + Classif      │
│  POST /api/confirm     → Confirmation catégorie             │
│  POST /api/query       → Question RAG (filtre cat/fichier)  │
│  GET  /api/documents   → Liste des documents indexés        │
│  GET  /api/categories  → Stats par catégorie                │
│  GET  /api/health      → Statut du système                  │
│                                                             │
└──────┬──────────────────────┬───────────────────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐    ┌─────────────────────────┐
│  MODULE IA   │    │    BASE DE DONNÉES      │
│              │    │                         │
│ • Classifieur│    │ • ChromaDB (vecteurs)   │
│   zero-shot  │    │   - texte               │
│   (Ollama)   │    │   - catégorie           │
│              │    │   - source              │
│ • RAG        │    │   - date d'ajout        │
│   (Ollama)   │    │                         │
│              │    │ • Stockage fichiers     │
│ • Embeddings │    │   (data/uploads/)       │
│   (local)    │    │                         │
└──────────────┘    └─────────────────────────┘

🔒 TOUT EST LOCAL — AUCUNE DONNÉE NE SORT
📡 OFFLINE : fonctionne sans internet une fois les modèles téléchargés
```

---

## 🗺️ ROADMAP GLOBALE RÉVISÉE (Jours 3-10)

> **Principe clé :** Chaque jour, chaque personne a un livrable **indépendant** qu'elle peut réaliser seule, de chez elle, sans attendre les autres. La fusion se fait en fin de journée via Git.

| Jour | Phase | @A1 (Cerveau IA) | @A2 (Tuyauterie) | @B1 (Interface) | @B2 (Preuve) |
|------|-------|-------------------|-------------------|------------------|--------------|
| **3** | Classification + Architecture | Module classifieur zero-shot | ChromaDB avec métadonnées + ingestion | Maquette UI complète (toutes les pages) | Classer les docs + jeu de test classif + RAG |
| **4** | RAG + API | Pipeline RAG avec filtres (catégorie, fichier) | API FastAPI complète (tous les endpoints) | UI Upload + Classification (données simulées) | Commencer le rapport + doc architecture |
| **5** | Intégration 1 | Fusion classifieur + API | Fusion API + ChromaDB | UI RAG avec filtres + sélection fichier | Tests manuels classifieur (20 docs) |
| **6** | Intégration 2 | Optimisation prompts + gestion erreurs | Gestion upload backend + persistance | UI complète connectée + design final | Tests manuels RAG (30 questions) |
| **7** | Évaluation | Métriques classification (précision, rappel) | Métriques RAG + performances techniques | Visualisations des résultats | Compiler toutes les évaluations |
| **8** | Limites + Coût | Analyse limites IA + biais | Étude coût matériel + offline | Limites UX | Rapport limites + biais |
| **9** | Rapport + Nettoyage | Nettoyage code IA | Script de lancement + README | Slides de démo | Rapport final complet |
| **10** | Livraison | Tests finaux + démo technique | Vérification offline + installation | Répétition démo | Checklist livrables |

---

## 🚀 JOUR 3 — Classification Zero-Shot + ChromaDB + Maquette UI

> **Objectif global :** À la fin du Jour 3, chaque module principal existe **indépendamment** et fonctionne seul. Demain, on les connecte.

> **Règle du jour :** Chacun travaille **de son côté**. Pas besoin d'attendre les autres. On fusionne via Git en fin de journée.

---

### 📅 Planning du Jour 3

| Horaire | Durée | Activité | Qui |
|---------|-------|----------|-----|
| 09h00 - 09h20 | 20 min | **Stand-up + présentation de la nouvelle architecture** | Tous |
| 09h20 - 12h00 | 2h40 | **Travail indépendant** (chacun sur son module) | Chacun |
| 12h00 - 14h00 | 2h | Pause | — |
| 14h00 - 16h30 | 2h30 | **Travail indépendant** (suite) | Chacun |
| 16h30 - 17h00 | 30 min | **Fusion Git + Tests croisés** | Tous |
| 17h00 - 17h30 | 30 min | **Debrief** | Tous |

---

## 🧠 PARTIE A1 : Module Classifieur Zero-Shot

> **Objectif :** Créer un module Python qui prend un texte, l'envoie au LLM local, et retourne la catégorie prédite + un score de confiance.
> **Indépendance :** A1 n'a besoin que d'Ollama (déjà installé) et des textes extraits au Jour 2. Pas besoin de l'API, de l'interface, ni de ChromaDB.
> **Livrable du jour :** `src/rag/classifier.py` fonctionnel + test sur 5 documents.

### Étape A1.1 : Concevoir le prompt de classification

Le prompt est le cœur du classifieur. Il doit être **précis, contraignant, et retourner du JSON** pour qu'on puisse le parser automatiquement.

Crée le fichier `src/rag/classifier.py` :

```python
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
```

---

### Étape A1.2 : Tester le classifieur

Dans PowerShell, depuis la racine du projet :

```
python src/rag/classifier.py
```

**Résultat attendu :**
```
🧪 Test du classifieur zero-shot

📄 Extrait règlement :
   Catégorie : Règlements
   Confiance : 92%
   Justification : Le texte contient des articles numérotés avec des obligations et des sanctions.

📄 Extrait guide :
   Catégorie : Guides pratiques
   Confiance : 88%
   Justification : Le texte donne des conseils pratiques sous forme de tutoriel.

📄 Extrait procédure :
   Catégorie : Procédures
   Confiance : 95%
   Justification : Le texte décrit des étapes numérotées dans un ordre séquentiel.
```

**🧪 Tests de validation :**
- [ ] Le script s'exécute sans erreur
- [ ] Les 3 textes de test sont classés correctement
- [ ] Le score de confiance est > 80% pour les cas clairs
- [ ] Le JSON est parsé correctement (pas d'erreur de format)
- [ ] Le temps de réponse est < 10 secondes par classification

---

### Étape A1.3 : Tester sur les vrais documents

Prends 5 fichiers de `data/processed/` et classifie-les :

```python
# Ajouter à la fin de classifier.py ou dans un script séparé
import os

for filename in os.listdir("data/processed/")[:5]:
    filepath = os.path.join("data/processed", filename)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    result = classify_document(text)
    print(f"📄 {filename}")
    print(f"   → {result['categorie']} ({result['confiance']:.0%})")
    print(f"   → {result['justification']}\n")
```

**🧪 Tests de validation :**
- [ ] 5 documents réels classifiés
- [ ] Les résultats sont cohérents (un règlement n'est pas classé comme formulaire)
- [ ] Les cas ambigus ont un score de confiance < 80%

---

### Étape A1.4 : Tester la fonction d'alternatives

```python
# Tester avec un texte ambigu
texte_ambigu = "Le formulaire de demande de bourse doit être déposé "
"conformément au règlement intérieur de l'université, selon la procédure "
"suivante : étape 1, remplir le formulaire..."

result = classify_with_alternatives(texte_ambigu)
print(f"Principal : {result['primary']['categorie']} "
      f"({result['primary']['confiance']:.0%})")
print(f"Confirmation nécessaire : {result['needs_confirmation']}")
if result['alternatives']:
    print("Alternatives :")
    for alt in result['alternatives']:
        print(f"  - {alt['categorie']} : {alt['probabilite']:.0%}")
```

**🧪 Tests de validation :**
- [ ] La fonction retourne des alternatives quand la confiance est basse
- [ ] `needs_confirmation` est `True` pour les cas ambigus
- [ ] `needs_confirmation` est `False` pour les cas clairs

---

### ✅ Checklist A1 — Fin du Jour 3
- [ ] `src/rag/classifier.py` créé avec `classify_document()` et `classify_with_alternatives()`
- [ ] 3 textes de test classés correctement
- [ ] 5 documents réels classés avec résultats cohérents
- [ ] Fonction d'alternatives fonctionnelle
- [ ] Temps de classification < 10 secondes par document
- [ ] Commit Git : `git add src/rag/classifier.py && git commit -m "Jour 3 : classifieur zero-shot"`

---

## 🔧 PARTIE A2 : ChromaDB avec Métadonnées + Ingestion

> **Objectif :** Créer le système d'ingestion qui stocke les chunks dans ChromaDB avec les métadonnées (catégorie, source, date). Classifier manuellement les documents existants dans les 5 catégories.
> **Indépendance :** A2 n'a besoin que des fichiers de `data/processed/` et de `data/chunks/` (faits au Jour 2). Pas besoin du classifieur de A1 ni de l'interface de B1.
> **Livrable du jour :** `src/ingestion/ingest.py` + base ChromaDB peuplée avec métadonnées.

### Étape A2.1 : Classifier manuellement les documents existants

En attendant que le classifieur automatique de A1 soit prêt (on l'intégrera demain), **A2 classe manuellement** les documents existants dans les 5 catégories.

Crée le fichier `data/documents_registry.json` :

```json
{
    "01_reglement_interieur.txt": {
        "categorie": "Règlements",
        "date_ajout": "2025-01-15",
        "type_original": "PDF",
        "pages": 25
    },
    "02_guide_bourses.txt": {
        "categorie": "Guides pratiques",
        "date_ajout": "2025-01-15",
        "type_original": "PDF",
        "pages": 8
    },
    "03_procedure_inscription.txt": {
        "categorie": "Procédures",
        "date_ajout": "2025-01-15",
        "type_original": "PDF",
        "pages": 5
    },
    "04_calendrier_academique.txt": {
        "categorie": "Organisation & plannings",
        "date_ajout": "2025-01-15",
        "type_original": "PDF",
        "pages": 2
    },
    "05_formulaire_demande.txt": {
        "categorie": "Formulaires & documents ponctuels",
        "date_ajout": "2025-01-15",
        "type_original": "PDF",
        "pages": 1
    }
}
```

**⚠️ Adapte ce fichier à TES vrais documents.** Ouvre chaque fichier de `data/processed/`, lis les premières lignes, et attribue la bonne catégorie.

**🧪 Tests de validation :**
- [ ] Chaque fichier de `data/processed/` a une entrée dans le registre
- [ ] Les 5 catégories sont représentées (au moins 1 document par catégorie si possible)
- [ ] Les attributions sont logiques

---

### Étape A2.2 : Créer le script d'ingestion dans ChromaDB

Crée le fichier `src/ingestion/ingest.py` :

```python
import os
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configuration
PROCESSED_DIR = "data/processed"
CHUNKS_FILE = "data/chunks/all_chunks.json"
REGISTRY_FILE = "data/documents_registry.json"
CHROMA_DIR = "data/chroma_db"

# Catégories officielles
CATEGORIES = [
    "Règlements",
    "Guides pratiques",
    "Procédures",
    "Organisation & plannings",
    "Formulaires & documents ponctuels"
]

def create_chroma_collection():
    """Crée ou charge la collection ChromaDB"""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Supprimer l'ancienne collection si elle existe (pour repartir de zéro)
    try:
        client.delete_collection("documents")
    except:
        pass
    
    collection = client.create_collection(
        name="documents",
        metadata={"description": "Documents institutionnels classifiés"}
    )
    return collection

def load_chunks():
    """Charge les chunks depuis le fichier JSON"""
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_registry():
    """Charge le registre des documents"""
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def ingest_all():
    """Ingestion complète de tous les chunks dans ChromaDB"""
    print("🚀 Démarrage de l'ingestion...\n")
    
    # 1. Charger les données
    chunks = load_chunks()
    registry = load_registry()
    print(f"📦 {len(chunks)} chunks chargés")
    print(f"📋 {len(registry)} documents dans le registre\n")
    
    # 2. Créer la collection ChromaDB
    collection = create_chroma_collection()
    print("🗄️ Collection ChromaDB créée\n")
    
    # 3. Charger le modèle d'embedding
    print("📐 Chargement du modèle d'embedding...")
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    print("✅ Modèle chargé\n")
    
    # 4. Préparer les données pour ChromaDB
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        source = chunk["source"]
        
        # Récupérer la catégorie depuis le registre
        if source in registry:
            categorie = registry[source]["categorie"]
            date_ajout = registry[source]["date_ajout"]
        else:
            categorie = "Non classifié"
            date_ajout = "inconnu"
        
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append({
            "source": source,
            "categorie": categorie,
            "chunk_index": chunk["chunk_index"],
            "date_ajout": date_ajout,
            "char_count": chunk["char_count"]
        })
    
    # 5. Calculer les embeddings
    print(f"📐 Calcul des embeddings pour {len(documents)} chunks...")
    embeddings = model.encode(documents, show_progress_bar=True)
    embeddings_list = embeddings.tolist()
    print("✅ Embeddings calculés\n")
    
    # 6. Insérer dans ChromaDB (par lots de 100)
    BATCH_SIZE = 100
    for i in range(0, len(ids), BATCH_SIZE):
        end = min(i + BATCH_SIZE, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            embeddings=embeddings_list[i:end]
        )
        print(f"  ✅ Lot {i//BATCH_SIZE + 1} : chunks {i+1}-{end} insérés")
    
    # 7. Résumé
    print(f"\n{'='*50}")
    print(f"📊 INGESTION TERMINÉE")
    print(f"   Chunks indexés : {collection.count()}")
    print(f"   Catégories :")
    
    for cat in CATEGORIES:
        count = len([m for m in metadatas if m["categorie"] == cat])
        print(f"     • {cat} : {count} chunks")
    
    unclassified = len([m for m in metadatas if m["categorie"] == "Non classifié"])
    if unclassified > 0:
        print(f"     ⚠️ Non classifiés : {unclassified} chunks")
    
    print(f"\n📁 Base sauvegardée dans : {CHROMA_DIR}/")

if __name__ == "__main__":
    ingest_all()
```

---

### Étape A2.3 : Lancer l'ingestion

```
python src/ingestion/ingest.py
```

**Résultat attendu :**
```
🚀 Démarrage de l'ingestion...

📦 281 chunks chargés
📋 15 documents dans le registre

🗄️ Collection ChromaDB créée

📐 Chargement du modèle d'embedding...
✅ Modèle chargé

📐 Calcul des embeddings pour 281 chunks...
✅ Embeddings calculés

  ✅ Lot 1 : chunks 1-100 insérés
  ✅ Lot 2 : chunks 101-200 insérés
  ✅ Lot 3 : chunks 201-281 insérés

==================================================
📊 INGESTION TERMINÉE
   Chunks indexés : 281
   Catégories :
     • Règlements : 82 chunks
     • Guides pratiques : 45 chunks
     • Procédures : 67 chunks
     • Organisation & plannings : 38 chunks
     • Formulaires & documents ponctuels : 49 chunks

📁 Base sauvegardée dans : data/chroma_db/
```

**🧪 Tests de validation :**
- [ ] Le script s'exécute sans erreur
- [ ] Tous les chunks sont indexés (le nombre correspond au Jour 2)
- [ ] Les 5 catégories sont représentées
- [ ] Le dossier `data/chroma_db/` contient des fichiers

---

### Étape A2.4 : Tester la recherche avec filtre par catégorie

Ajoute ce test à la fin de `ingest.py` ou dans un script séparé `src/ingestion/test_search.py` :

```python
import chromadb

CHROMA_DIR = "data/chroma_db"

def test_search():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection("documents")
    
    # Test 1 : Recherche sans filtre
    print("🔍 Test 1 : Recherche générale")
    results = collection.query(
        query_texts=["Quelles sont les conditions pour obtenir une bourse ?"],
        n_results=3
    )
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        print(f"  {i+1}. [{meta['categorie']}] {meta['source']}")
        print(f"     {doc[:100]}...\n")
    
    # Test 2 : Recherche AVEC filtre par catégorie
    print("🔍 Test 2 : Recherche filtrée (Règlements uniquement)")
    results = collection.query(
        query_texts=["Quelles sont les sanctions en cas de fraude ?"],
        n_results=3,
        where={"categorie": "Règlements"}
    )
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        print(f"  {i+1}. [{meta['categorie']}] {meta['source']}")
        print(f"     {doc[:100]}...\n")
    
    # Test 3 : Recherche filtrée par fichier
    print("🔍 Test 3 : Recherche dans un fichier spécifique")
    results = collection.query(
        query_texts=["Quelles sont les étapes ?"],
        n_results=3,
        where={"source": "03_procedure_inscription.txt"}
    )
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        print(f"  {i+1}. [{meta['categorie']}] {meta['source']}")
        print(f"     {doc[:100]}...\n")

if __name__ == "__main__":
    test_search()
```

```
python src/ingestion/test_search.py
```

**🧪 Tests de validation :**
- [ ] La recherche générale retourne des résultats pertinents
- [ ] Le filtre par catégorie fonctionne (seuls les "Règlements" apparaissent)
- [ ] Le filtre par fichier fonctionne (seul le fichier spécifié apparaît)
- [ ] Les métadonnées sont correctement attachées à chaque résultat

---

### ✅ Checklist A2 — Fin du Jour 3
- [ ] `data/documents_registry.json` créé avec tous les documents classifiés
- [ ] `src/ingestion/ingest.py` créé et fonctionnel
- [ ] ChromaDB peuplé avec métadonnées (catégorie, source, date)
- [ ] Modèle d'embedding téléchargé et fonctionnel
- [ ] Recherche avec filtre par catégorie testée
- [ ] Recherche avec filtre par fichier testée
- [ ] Commit Git : `git add . && git commit -m "Jour 3 : ChromaDB avec métadonnées + ingestion"`

---

## 🎨 PARTIE B1 : Maquette UI Complète (Toutes les Pages)

> **Objectif :** Créer l'interface Streamlit complète avec **toutes les pages et toutes les vues**, utilisant des données simulées. L'interface doit être **belle et professionnelle**.
> **Indépendance :** B1 n'a besoin que de Streamlit (installé au Jour 1). Pas besoin du backend, du classifieur, ni de ChromaDB. Tout est simulé.
> **Livrable du jour :** `interface/app.py` complet avec navigation multi-pages.

### Étape B1.1 : Créer l'architecture multi-pages

Streamlit supporte les multi-pages nativement. Crée cette structure :

```
interface/
├── app.py              (page d'accueil + navigation)
├── pages/
│   ├── 1_📤_Upload.py  (upload + classification)
│   ├── 2_💬_Questions.py (RAG + filtres)
│   └── 3_📊_Dashboard.py (statistiques)
└── assets/
    └── style.css       (CSS personnalisé)
```

---

### Étape B1.2 : Page d'accueil (`interface/app.py`)

```python
import streamlit as st

st.set_page_config(
    page_title="DocuClassif AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #F8F9FA;
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #1E3A5F;
        margin-bottom: 1rem;
    }
    .badge-offline {
        background: #28A745;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📚 DocuClassif AI")
    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("app.py", label="🏠 Accueil", icon="🏠")
    st.page_link("pages/1_📤_Upload.py", label="📤 Upload & Classification", icon="📤")
    st.page_link("pages/2_💬_Questions.py", label="💬 Questions & Réponses", icon="💬")
    st.page_link("pages/3_📊_Dashboard.py", label="📊 Tableau de bord", icon="📊")
    st.markdown("---")
    st.markdown("### 🔒 Système")
    st.markdown('<span class="badge-offline">🟢 100% OFFLINE</span>', 
                unsafe_allow_html=True)
    st.caption("Modèle : Llama 3.2 3B")
    st.caption("Moteur : Ollama (local)")
    st.caption("Base : ChromaDB (local)")
    st.caption("Aucune donnée envoyée à l'extérieur")

# Contenu principal
st.markdown('<div class="main-header">📚 DocuClassif AI</div>', 
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">Classification intelligente et assistant '
            'questions-réponses pour vos documents institutionnels</div>', 
            unsafe_allow_html=True)

st.markdown("---")

# Fonctionnalités
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📤 Classification Automatique</h3>
        <p>Uploadez un document PDF ou Word. Notre IA le classe automatiquement 
        dans l'une des 5 catégories institutionnelles. Vous gardez toujours 
        le contrôle : la classification doit être confirmée.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>🔒 Souveraineté des Données</h3>
        <p>Tout fonctionne localement sur votre machine. Aucune donnée n'est 
        envoyée à un service externe. Fonctionne même sans connexion internet.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>💬 Questions & Réponses</h3>
        <p>Posez des questions sur vos documents. Filtrez par catégorie ou 
        par fichier spécifique. Les réponses sont sourcées et vérifiables.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Tableau de Bord</h3>
        <p>Visualisez la répartition de vos documents par catégorie, 
        les statistiques d'utilisation et l'historique des classifications.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Les 5 catégories
st.markdown("### 📁 Les 5 Catégories de Documents")
cats = st.columns(5)
categories = [
    ("⚖️", "Règlements", "Lois, décrets, statuts"),
    ("📖", "Guides", "Manuels, tutoriels, FAQ"),
    ("🔄", "Procédures", "Étapes, workflows"),
    ("📅", "Organisation", "Planning, organigrammes"),
    ("📝", "Formulaires", "Attestations, demandes")
]
for col, (icon, name, desc) in zip(cats, categories):
    with col:
        st.markdown(f"#### {icon} {name}")
        st.caption(desc)
```

---

### Étape B1.3 : Page Upload & Classification (`interface/pages/1_📤_Upload.py`)

```python
import streamlit as st
import time

st.set_page_config(page_title="Upload & Classification", page_icon="📤", layout="wide")

st.title("📤 Upload & Classification de Documents")
st.caption("Uploadez un document, l'IA le classera automatiquement. "
           "Vous confirmez la catégorie.")

st.markdown("---")

# Zone d'upload
uploaded_file = st.file_uploader(
    "Glissez-déposez ou sélectionnez un fichier",
    type=["pdf", "docx", "txt"],
    help="Formats acceptés : PDF, Word, TXT"
)

if uploaded_file:
    # Infos sur le fichier
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Nom", uploaded_file.name)
    with col2:
        st.metric("📏 Taille", f"{uploaded_file.size / 1024:.1f} Ko")
    with col3:
        st.metric("📎 Type", uploaded_file.type)
    
    st.markdown("---")
    
    # Simulation de la classification
    st.subheader("🤖 Analyse en cours...")
    
    with st.spinner("Extraction du texte..."):
        time.sleep(1)
    with st.spinner("Classification par l'IA..."):
        time.sleep(2)
    
    # Résultat simulé (CAS 1 : Confiance haute)
    st.subheader("📊 Résultat de la Classification")
    
    confidence = 0.87  # Simulé — sera remplacé par le vrai classifieur
    
    if confidence >= 0.8:
        st.success(f"✅ **Catégorie proposée : Procédures** (confiance : {confidence:.0%})")
        st.info("💡 L'IA est confiante dans cette classification. "
                "Veuillez confirmer ou choisir une autre catégorie.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmer : Procédures", type="primary", 
                        use_container_width=True):
                st.balloons()
                st.success("Document classifié et indexé avec succès !")
        with col2:
            if st.button("🔄 Choisir une autre catégorie", 
                        use_container_width=True):
                st.session_state["show_alternatives"] = True
    else:
        # CAS 2 : Confiance basse
        st.warning(f"⚠️ **L'IA hésite** (confiance : {confidence:.0%})")
        st.info("Plusieurs catégories sont possibles. Veuillez choisir :")
        
        alternatives = [
            ("Procédures", 0.65),
            ("Guides pratiques", 0.20),
            ("Formulaires & documents ponctuels", 0.10)
        ]
        
        for cat, prob in alternatives:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{cat}**")
            with col2:
                st.progress(prob)
        
        selected = st.selectbox(
            "Choisissez la catégorie :",
            ["Règlements", "Guides pratiques", "Procédures", 
             "Organisation & plannings", "Formulaires & documents ponctuels"]
        )
        
        if st.button("✅ Confirmer la sélection", type="primary"):
            st.success(f"Document classifié dans '{selected}' et indexé !")

    # Aperçu du texte extrait
    st.markdown("---")
    with st.expander("👁️ Aperçu du texte extrait"):
        st.text("Ceci est un aperçu simulé du texte extrait du document.\n"
                "En production, le vrai texte apparaîtra ici.\n\n"
                "Étape 1 : Déposez votre dossier au bureau...\n"
                "Étape 2 : Attendez la confirmation...\n"
                "Étape 3 : Présentez-vous à l'entretien...")
```

---

### Étape B1.4 : Page Questions & Réponses (`interface/pages/2_💬_Questions.py`)

```python
import streamlit as st
import time

st.set_page_config(page_title="Questions & Réponses", page_icon="💬", layout="wide")

st.title("💬 Assistant Questions-Réponses")
st.caption("Posez des questions sur vos documents institutionnels")

# Sidebar : Filtres
with st.sidebar:
    st.markdown("### 🔍 Filtres")
    
    search_scope = st.radio(
        "Portée de la recherche :",
        ["Tous les documents", "Par catégorie", "Par fichier"],
        index=0
    )
    
    if search_scope == "Par catégorie":
        selected_cat = st.selectbox(
            "Catégorie :",
            ["Règlements", "Guides pratiques", "Procédures",
             "Organisation & plannings", "Formulaires & documents ponctuels"]
        )
        st.info(f"🔎 Recherche limitée à : **{selected_cat}**")
    
    elif search_scope == "Par fichier":
        selected_file = st.selectbox(
            "Fichier :",
            ["01_reglement_interieur.txt", "02_guide_bourses.txt",
             "03_procedure_inscription.txt", "04_calendrier.txt",
             "05_formulaire_demande.txt"]
        )
        st.info(f"🔎 Recherche limitée à : **{selected_file}**")
    
    st.markdown("---")
    st.markdown("### ⚙️ Options")
    n_sources = st.slider("Nombre de sources à afficher", 1, 5, 3)

# Zone de question principale
question = st.chat_input("💬 Posez votre question ici...")

if question:
    # Afficher la question de l'utilisateur
    with st.chat_message("user"):
        st.markdown(question)
    
    # Réponse simulée de l'assistant
    with st.chat_message("assistant"):
        with st.spinner("🔍 Recherche dans les documents..."):
            time.sleep(2)
        
        st.markdown("""
        D'après les documents disponibles, voici la réponse :
        
        Les conditions pour obtenir une bourse d'études sont les suivantes :
        1. Être inscrit en formation initiale à l'université
        2. Avoir une moyenne générale supérieure à 12/20
        3. Fournir un dossier complet comprenant : CIN, relevé de notes, 
           certificat de scolarité et attestation de revenus des parents
        
        Le dossier doit être déposé au bureau de la scolarité avant le 30 octobre.
        """)
        
        # Sources
        st.markdown("---")
        st.markdown("#### 📎 Sources")
        
        sources = [
            ("02_guide_bourses.txt", "Guides pratiques", "Page 3, §2"),
            ("01_reglement_interieur.txt", "Règlements", "Article 45"),
            ("03_procedure_inscription.txt", "Procédures", "Étape 4")
        ]
        
        for i, (file, cat, ref) in enumerate(sources[:n_sources]):
            with st.expander(f"📄 Source {i+1} : {file}"):
                st.markdown(f"**Catégorie :** {cat}")
                st.markdown(f"**Référence :** {ref}")
                st.markdown("*Extrait du document simulé...*")
    
    # Métadonnées de la réponse
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏱️ Temps", "3.2s")
    with col2:
        st.metric("📄 Sources", f"{n_sources}")
    with col3:
        st.metric("🎯 Pertinence", "92%")
```

---

### Étape B1.5 : Page Dashboard (`interface/pages/3_📊_Dashboard.py`)

```python
import streamlit as st

st.set_page_config(page_title="Tableau de bord", page_icon="📊", layout="wide")

st.title("📊 Tableau de Bord")
st.caption("Vue d'ensemble de votre base documentaire")

# Statistiques générales
st.markdown("### 📈 Statistiques Générales")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📄 Documents", "15", "+3 cette semaine")
with col2:
    st.metric("✂️ Chunks", "281")
with col3:
    st.metric("❓ Questions posées", "47")
with col4:
    st.metric("✅ Classifications", "12", "100% confirmées")

st.markdown("---")

# Répartition par catégorie
st.markdown("### 📁 Répartition par Catégorie")

col1, col2 = st.columns(2)

with col1:
    # Données simulées
    categories = {
        "⚖️ Règlements": 82,
        "📖 Guides pratiques": 45,
        "🔄 Procédures": 67,
        "📅 Organisation": 38,
        "📝 Formulaires": 49
    }
    st.bar_chart(categories)

with col2:
    for cat, count in categories.items():
        st.markdown(f"**{cat}** : {count} chunks")
        st.progress(count / 82)

st.markdown("---")

# Documents récents
st.markdown("### 🕐 Documents Récemment Ajoutés")
st.table({
    "Fichier": ["rapport_annuel.pdf", "guide_inscription.pdf", "formulaire_stage.docx"],
    "Catégorie": ["Organisation", "Guides pratiques", "Formulaires"],
    "Date": ["2025-01-15", "2025-01-14", "2025-01-13"],
    "Statut": ["✅ Confirmé", "✅ Confirmé", "⏳ En attente"]
})
```

---

### Étape B1.6 : Lancer et tester

```
streamlit run interface/app.py
```

**🧪 Tests de validation :**
- [ ] La page d'accueil s'affiche avec les 4 fonctionnalités
- [ ] La sidebar de navigation fonctionne (clic sur chaque page)
- [ ] La page Upload : on peut uploader un fichier, la classification simulée s'affiche
- [ ] La page Upload : le bouton "Confirmer" fonctionne
- [ ] La page Upload : le cas "confiance basse" affiche les alternatives
- [ ] La page Questions : on peut taper une question, la réponse simulée s'affiche
- [ ] La page Questions : les filtres (catégorie, fichier) sont visibles
- [ ] La page Questions : les sources sont affichées
- [ ] La page Dashboard : les graphiques et tableaux s'affichent
- [ ] Le badge "100% OFFLINE" est visible dans la sidebar
- [ ] Le design est propre et professionnel

---

### ✅ Checklist B1 — Fin du Jour 3
- [ ] `interface/app.py` (accueil) créé
- [ ] `interface/pages/1_📤_Upload.py` créé
- [ ] `interface/pages/2_💬_Questions.py` créé
- [ ] `interface/pages/3_📊_Dashboard.py` créé
- [ ] Navigation multi-pages fonctionnelle
- [ ] Upload + classification simulée (cas confiance haute + basse)
- [ ] RAG simulé avec filtres (catégorie + fichier)
- [ ] Dashboard avec graphiques
- [ ] Design professionnel (CSS, couleurs, layout)
- [ ] Badge "100% OFFLINE" visible
- [ ] Commit Git : `git add interface/ && git commit -m "Jour 3 : maquette UI complète"`

---

## 📝 PARTIE B2 : Classification Manuelle + Jeux de Test + Rapport

> **Objectif :** Classer tous les documents existants, créer les jeux de test pour la classification ET le RAG, commencer le rapport.
> **Indépendance :** B2 n'a besoin que des documents dans `data/processed/` et d'un traitement de texte. Pas besoin de code, pas besoin de Python.
> **Livrable du jour :** `tests/` complet + `docs/rapport.md` début + `data/documents_registry.json` (à partager avec A2).

### Étape B2.1 : Classer tous les documents dans les 5 catégories

Ouvre **chaque** fichier de `data/processed/` et attribue-lui une catégorie.

| Catégorie | Ce qui rentre dedans | Mots-clés typiques |
|-----------|---------------------|-------------------|
| **Règlements** | Textes normatifs, contraignants | Article, alinéa, décret, loi, obligation, sanction, interdit |
| **Guides pratiques** | Manuels, conseils, FAQ | Comment, guide, conseil, astuce, FAQ, tutoriel, étape |
| **Procédures** | Séquences d'actions | Étape 1, d'abord, ensuite, formulaire à déposer, délai |
| **Organisation & plannings** | Structures, calendriers | Organigramme, calendrier, planning, semestre, horaire, service |
| **Formulaires & documents ponctuels** | Docs à remplir | Formulaire, attestation, demande, déclaration, signature, cachet |

Crée le fichier `data/documents_registry.json` (même format que pour A2 — vous vous coordonnerez en fin de journée).

**🧪 Tests de validation :**
- [ ] Chaque document a une catégorie
- [ ] Les 5 catégories sont représentées
- [ ] Pas de document "fourre-tout" dans une seule catégorie

---

### Étape B2.2 : Jeu de test Classification

Crée `tests/test_classification.md` avec **15-20 extraits de texte** + la catégorie attendue.

Format :

```markdown
## Test Classification Zero-Shot

### TC01 [Facile — Règlements]
**Extrait :** "Article 15 : Tout étudiant convaincu de fraude lors d'un examen 
sera immédiatement exclu de l'établissement pour une durée minimale de 2 ans."
**Catégorie attendue :** Règlements
**Confiance attendue :** > 85%

### TC02 [Facile — Formulaires]
**Extrait :** "FORMULAIRE DE DEMANDE DE BOURSE — Année universitaire 2024-2025
Nom : ___ Prénom : ___ Date de naissance : ___ CIN : ___"
**Catégorie attendue :** Formulaires & documents ponctuels
**Confiance attendue :** > 90%

### TC03 [Moyen — Procédures]
**Extrait :** "Pour obtenir votre diplôme, suivez les étapes suivantes : 
1) Vérifiez que tous vos crédits sont validés. 2) Déposez une demande 
de diplôme au secrétariat. 3) Attendez la convocation pour la cérémonie."
**Catégorie attendue :** Procédures
**Confiance attendue :** > 75%

### TC04 [Difficile — Ambigu]
**Extrait :** "Le règlement intérieur prévoit que les étudiants doivent 
suivre la procédure d'inscription décrite dans le guide de rentrée, 
en remplissant le formulaire F-2024 avant la date limite du calendrier."
**Catégorie attendue :** Règlements (car c'est le texte normatif qui prime)
**Confiance attendue :** < 70% (ambigu, mentionne 4 catégories)
**Note :** Ce cas doit déclencher la demande de confirmation utilisateur

### TC05 [Hors domaine]
**Extrait :** "La recette du ravitoto : prendre des feuilles de manioc, 
les piler finement, ajouter du porc et du lait de coco..."
**Catégorie attendue :** Aucune / Inconnu
**Confiance attendue :** < 50%
```

**🧪 Tests de validation :**
- [ ] 15-20 extraits de test rédigés
- [ ] Mix : facile, moyen, difficile, ambigu, hors-domaine
- [ ] Les 5 catégories sont testées
- [ ] Au moins 2 cas ambigus (confiance basse attendue)
- [ ] Au moins 1 cas hors-domaine

---

### Étape B2.3 : Jeu de test RAG

Crée `tests/test_rag.md` avec **20 questions** + réponses attendues + filtres.

Format :

```markdown
## Test RAG avec Filtres

### TR01 [Général]
**Question :** Quelles sont les conditions pour obtenir une bourse ?
**Filtre :** Aucun (tous les documents)
**Réponse attendue :** Moyenne > 12/20, dossier complet, dépôt avant le 30/10
**Sources attendues :** 02_guide_bourses.txt
**Catégorie attendue dans les sources :** Guides pratiques

### TR02 [Filtré par catégorie]
**Question :** Quelles sont les sanctions en cas de fraude ?
**Filtre :** Catégorie = Règlements
**Réponse attendue :** Exclusion de 2 ans minimum
**Sources attendues :** 01_reglement_interieur.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître

### TR03 [Filtré par fichier]
**Question :** Quelles sont les étapes à suivre ?
**Filtre :** Fichier = 03_procedure_inscription.txt
**Réponse attendue :** Les étapes spécifiques de l'inscription
**Vérification :** Seule la source 03_procedure_inscription.txt doit apparaître

### TR04 [Hors corpus]
**Question :** Quel est le cours du Bitcoin aujourd'hui ?
**Filtre :** Aucun
**Réponse attendue :** "Je ne trouve pas cette information dans les documents"
**Vérification :** Le modèle ne doit PAS inventer de réponse

### TR05 [Malgache]
**Question :** Inona ny fepetra takiana hangataka bourse ?
**Filtre :** Aucun
**Réponse attendue :** Réponse en français ou indication qu'il ne comprend pas le malgache
**Vérification :** Pas d'hallucination en malgache
```

**🧪 Tests de validation :**
- [ ] 20 questions rédigées
- [ ] Mix : général, filtré par catégorie, filtré par fichier, hors-sujet, malgache
- [ ] Chaque question a une réponse attendue vérifiable
- [ ] Les filtres sont spécifiés

---

### Étape B2.4 : Commencer le rapport

Crée `docs/rapport.md` avec la structure initiale :

```markdown
# Rapport — Assistant RAG avec Classification de Documents

## 1. Introduction
- Contexte du projet
- Objectifs : classification + RAG local
- Enjeu de souveraineté des données

## 2. Architecture Technique
- Schéma global (à insérer)
- Stack : Ollama + LangChain + ChromaDB + FastAPI + Streamlit
- Les 5 catégories de documents
- Workflow : Upload → Classification → Confirmation → Indexation → RAG

## 3. Corpus de Données
- Description des documents
- Répartition par catégorie
- Qualité de l'extraction

## 4. Module Classification
- Approche zero-shot avec LLM
- Prompt de classification
- Résultats (à compléter Jour 7)

## 5. Module RAG
- Architecture du pipeline
- Filtres (catégorie, fichier)
- Résultats (à compléter Jour 7)

## 6. Évaluation
- Métriques classification (à compléter)
- Métriques RAG (à compléter)
- Performances techniques (à compléter)

## 7. Limites et Biais
- Limites techniques (à compléter)
- Biais du modèle (à compléter)
- Limites linguistiques (malgache)

## 8. Étude de Coût
- Configuration actuelle
- Configuration recommandée
- Comparaison local vs cloud

## 9. Conclusion
```

Rédige les sections 1, 2 et 3 (tu as déjà les infos).

**🧪 Tests de validation :**
- [ ] Structure du rapport complète
- [ ] Sections 1-3 rédigées
- [ ] Schéma d'architecture décrit

---

### ✅ Checklist B2 — Fin du Jour 3
- [ ] Tous les documents classifiés dans les 5 catégories
- [ ] `data/documents_registry.json` créé (à synchroniser avec A2)
- [ ] `tests/test_classification.md` : 15-20 extraits de test
- [ ] `tests/test_rag.md` : 20 questions avec filtres
- [ ] `docs/rapport.md` : structure + sections 1-3 rédigées
- [ ] Commit Git : `git add tests/ docs/ data/documents_registry.json && git commit -m "Jour 3 : jeux de test + rapport + registre"`

---

## 🔄 PARTIE FINALE : Fusion et Debrief (16h30-17h30)

### Étape 1 : Fusion Git (15 min)

Chacun pousse son travail :

```
git add .
git commit -m "Jour 3 : [ton module]"
git push
```

Puis chacun tire le travail des autres :

```
git pull
```

**🧪 Tests de validation :**
- [ ] Pas de conflits Git (si conflits, @A2 résout)
- [ ] Tous les fichiers des 4 personnes sont dans le dépôt

---

### Étape 2 : Synchronisation A2 ↔ B2 (10 min)

**Point critique :** A2 et B2 ont tous les deux créé `data/documents_registry.json`. Il faut fusionner :
- B2 a fait la classification manuelle (le contenu)
- A2 a fait le format technique (la structure)
- **Décision :** on garde la version de B2 (qui a lu les documents) et A2 vérifie que le format est correct pour son script d'ingestion.

---

### Étape 3 : Tests croisés (20 min)

| Qui teste quoi | Comment |
|----------------|---------|
| @A1 teste l'interface de @B1 | `streamlit run interface/app.py` |
| @B1 teste le classifieur de @A1 | `python src/rag/classifier.py` |
| @B2 teste la recherche de @A2 | `python src/ingestion/test_search.py` |
| @A2 teste les jeux de test de @B2 | Lit `tests/test_classification.md` |

---

### Étape 4 : Debrief (15 min)

1. **Qu'est-ce qui est fait ?** (cocher les checklists)
2. **Qu'est-ce qui bloque ?**
3. **Plan pour demain (Jour 4) :**
   - @A1 : Pipeline RAG avec filtres
   - @A2 : API FastAPI complète
   - @B1 : UI Upload connectée au vrai classifieur
   - @B2 : Rapport + documentation

---

## 📋 CHECKLIST GLOBALE DU JOUR 3

### 🧠 @A1 — Classifieur Zero-Shot
- [ ] `src/rag/classifier.py` créé
- [ ] Fonction `classify_document()` fonctionnelle
- [ ] Fonction `classify_with_alternatives()` fonctionnelle
- [ ] 3 textes de test + 5 documents réels classés
- [ ] Temps < 10s par classification
- [ ] Commit poussé

### 🔧 @A2 — ChromaDB + Ingestion
- [ ] `data/documents_registry.json` créé (synchronisé avec B2)
- [ ] `src/ingestion/ingest.py` créé et fonctionnel
- [ ] ChromaDB peuplé avec métadonnées
- [ ] Recherche filtrée par catégorie testée
- [ ] Recherche filtrée par fichier testée
- [ ] Commit poussé

### 🎨 @B1 — Maquette UI Complète
- [ ] 4 pages créées (Accueil, Upload, Questions, Dashboard)
- [ ] Navigation multi-pages fonctionnelle
- [ ] Upload avec cas confiance haute + basse
- [ ] RAG avec filtres (catégorie + fichier)
- [ ] Dashboard avec graphiques
- [ ] Design professionnel + badge OFFLINE
- [ ] Commit poussé

### 📝 @B2 — Tests + Rapport
- [ ] Documents classifiés dans les 5 catégories
- [ ] `tests/test_classification.md` (15-20 extraits)
- [ ] `tests/test_rag.md` (20 questions avec filtres)
- [ ] `docs/rapport.md` (structure + sections 1-3)
- [ ] Commit poussé

### 🔄 Équipe
- [ ] Fusion Git réussie (pas de conflits)
- [ ] Synchronisation A2 ↔ B2 sur le registre
- [ ] Tests croisés effectués
- [ ] Debrief fait
- [ ] Board Linear/Notion à jour

---

## 🎯 À la fin du Jour 3, l'équipe doit pouvoir dire :

> *"On a 4 modules indépendants qui fonctionnent chacun de leur côté : un classifieur zero-shot qui classe les textes dans les 5 catégories, une base ChromaDB avec métadonnées qui supporte les filtres, une interface complète avec toutes les pages, et des jeux de test complets. Demain, on les connecte ensemble via l'API."*

**Le plus dur est derrière vous.** Les fondations sont posées. Les Jours 4-6, c'est de l'assemblage. 🚀