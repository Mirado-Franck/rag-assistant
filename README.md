# Assistant RAG — Projet IA locale

Assistant de questions-réponses sur un corpus de documents institutionnels, conçu pour utiliser un modèle exécuté localement.

## Équipe

- A1 : ingénierie IA / RAG
- A2 : backend / API
- B1 : interface
- B2 : qualité / rapport

## Stack prévue

- Ollama + Llama 3.2
- LangChain + ChromaDB
- FastAPI + Streamlit
- Python 3.11 ou supérieur

## Structure

```text
rag-assistant/
├── data/
│   ├── raw/          # Documents d'origine et fichiers téléversés
│   └── processed/    # Données préparées
├── src/
│   ├── ingestion/    # Extraction et découpage existants
│   ├── rag/          # Réservé à la logique RAG
│   └── api/          # API FastAPI et routes
├── interface/        # Réservé à l'interface
├── tests/
├── docs/
├── requirements.txt
└── venv/             # Environnement local, à créer sur chaque machine
```

Les deux petits PDF de test du dépôt ont été conservés dans `data/raw/` sous des noms distincts. Les autres fichiers de données, l'environnement virtuel et les secrets ne sont pas versionnés.

## Installation

Créer et activer un environnement virtuel à la racine du dépôt, puis installer toutes les dépendances déclarées :

### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Vérification des principales dépendances du Jour 1 :

```bash
python -c "import fastapi, langchain, chromadb, streamlit; print('OK')"
```

## Lancement de l'API existante

Depuis la racine du dépôt, avec l'environnement virtuel activé :

```bash
python -m uvicorn src.api.main:app --reload
```

L'API et sa documentation interactive seront disponibles à `http://127.0.0.1:8000` et `http://127.0.0.1:8000/docs`.

> Le présent changement met en place la structure du Jour 1 et déplace le backend déjà présent. Il ne réalise pas les tâches du Jour 2 et ne prétend pas valider l'installation d'Ollama ou de Python sur les ordinateurs de l'équipe.
