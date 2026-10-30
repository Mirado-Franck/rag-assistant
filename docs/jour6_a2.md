# Jour 6 — Guide d'exécution A2

Ce guide prépare le contrôle local du backend. Les scripts de RAG appellent réellement Ollama; ils doivent être lancés sur la machine où le modèle et la base ChromaDB sont disponibles.

## 1. Préparer la machine

Depuis la racine du dépôt, activer le venv, installer les dépendances si nécessaire, puis vérifier le corpus :

```powershell
python -m pip install -r requirements.txt
python src/ingestion/ingest.py --validate-only
```

La collection `data/chroma_db` doit déjà contenir la collection `documents`. Si elle n'existe pas, créer l'index initial **avant** les uploads de test :

```powershell
python src/ingestion/ingest.py
```

Vérifier qu'Ollama est lancé et que le modèle configuré `llama3.2` est disponible (`ollama list`). Ne pas relancer une reconstruction Chroma (`--rebuild`) après les uploads confirmés sans sauvegarder les documents indexés.

Lancer ensuite l'API :

```powershell
python -m uvicorn src.api.main:app --reload
```

La documentation interactive s'ouvre sur `http://127.0.0.1:8000/docs`.

## 2. Vérifier les contrats et les cas limites

Dans un second terminal, depuis la racine du dépôt :

```powershell
python tests/api_smoke.py
```

Ce script vérifie les routes statistiques et plusieurs erreurs attendues sans ajouter de document à Chroma :

- question vide → HTTP 422;
- catégorie inexistante sur les routes query/documents → HTTP 400;
- fichier temporaire absent sur confirm → HTTP 404;
- extension interdite → HTTP 400;
- PDF illisible → HTTP 422.

Pour inclure un vrai appel de recherche/génération (ChromaDB, modèle d'embedding et Ollama requis) :

```powershell
python tests/api_smoke.py --check-rag
```

Les corps et réponses JSON attendus pour Streamlit sont récapitulés dans [`api_contract.md`](api_contract.md).

## 3. Stress-test RAG — 30 cas séquentiels

D'abord vérifier rapidement les trois premiers cas :

```powershell
python tests/rag_stress.py --limit 3
```

Si tout fonctionne, lancer les 30 questions :

```powershell
python tests/rag_stress.py
```

Le script mesure les durées murales et `temps_ms`, vérifie que l'API renvoie le schéma attendu, compare les sources observées aux sources attendues et enregistre chaque réponse. Les requêtes sont **séquentielles** pour ne pas saturer la machine locale. Les résultats détaillés sont écrits dans `tests/results/`, ignoré par Git; reporter les résultats réels et les erreurs dans le gabarit d'évaluation, pas dans le code.

Les 30 questions couvrent les 16 sources indexées initialement, les filtres catégorie/fichier, le hors-corpus et le malgache. Quand B2 ajoute des documents au corpus, vérifier que la collection et le registre ont été mis à jour, puis ajouter des cas ciblant ces nouvelles sources avant d'affirmer qu'elles ont été stress-testées.

## 4. Préparer l'évaluation et le rapport

- Remplir [`tests/evaluation_jour7_template.md`](../tests/evaluation_jour7_template.md) avec les résultats observés pour les 20 documents de classification et les 30 questions RAG.
- B2 reste responsable des mesures et de l'évaluation qualitative; A2 ne préremplit pas de résultats supposés.
- Reporter les métriques réelles dans la section 7 de [`rapport.md`](rapport.md), avec la machine, le corpus, les modèles et les conditions d'exécution.
- Dans `tests/test_rag.md`, corriger les noms de fichiers attendus s'ils ne correspondent pas aux sources du registre (ex. la procédure d'inscription est `05_procedure_inscription.txt` dans le corpus initial).
