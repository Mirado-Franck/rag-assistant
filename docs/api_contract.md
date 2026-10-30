# Contrat JSON de l'API (pour l'interface Streamlit)

Base URL locale par défaut : `http://127.0.0.1:8000`. Toutes les réponses sont en JSON, sauf le formulaire d'upload (`multipart/form-data`). Les noms de champs ci-dessous reflètent l'API actuelle.

## `GET /api/health`

Réponse `200` :

```json
{
  "status": "ok",
  "modele_llm": "llama3.2",
  "modele_embedding": "paraphrase-multilingual-MiniLM-L12-v2",
  "nb_documents": 16,
  "nb_chunks": 200,
  "categories": {
    "Règlements": 4,
    "Guides pratiques": 4,
    "Procédures": 3,
    "Organisation & plannings": 3,
    "Formulaires & documents ponctuels": 2
  }
}
```

Les nombres sont des exemples correspondant au corpus initial, ils évolueront avec le registre. `status == "ok"` signifie que l'API répond; cela ne garantit pas à lui seul qu'Ollama répond aux requêtes.

## `POST /api/upload`

Envoyer un fichier avec le champ de formulaire `file` (PDF, TXT ou DOCX; maximum 20 Mo). Exemple de réponse `200` :

```json
{
  "categorie": "Guides pratiques",
  "confiance": 0.93,
  "justification": "...",
  "alternatives": [],
  "needs_confirmation": false,
  "file_id": "a1b2c3d4",
  "filename": "guide.txt",
  "text_preview": "..."
}
```

`filename` est le nom d'origine. Le `file_id` doit être transmis à `/api/confirm`. Le classifieur de cette route doit être remplacé par l'intégration A1 lorsqu'elle sera prête; l'interface doit permettre de choisir/confirmer explicitement la catégorie.

Erreurs importantes : `400` (extension non supportée), `413` (fichier > 20 Mo), `422` (fichier illisible ou texte exploitable insuffisant).

## `POST /api/confirm`

Corps JSON :

```json
{
  "file_id": "a1b2c3d4",
  "categorie": "Guides pratiques"
}
```

Réponse `200` après indexation réussie :

```json
{
  "status": "success",
  "message": "...",
  "file_id": "a1b2c3d4",
  "source_file": "a1b2c3d4_guide.txt",
  "categorie": "Guides pratiques",
  "indexe": true,
  "chunks_count": 1
}
```

Utiliser `source_file` (nom stocké, préfixé par l'identifiant) comme valeur du filtre fichier de `/api/query`; ne pas utiliser le seul nom d'origine. Erreurs : `400` (catégorie ou identifiant invalide), `404` (upload temporaire absent), `422` (texte inexploitable), `503` (ChromaDB, modèle d'embedding ou index indisponible).

## `POST /api/query`

Corps JSON :

```json
{
  "question": "Quelles sont les règles de prêt à la bibliothèque ?",
  "n_results": 4,
  "category": "Règlements",
  "source_file": "06_reglement_bibliotheque.txt"
}
```

`question` est obligatoire (1–2000 caractères). `n_results` est facultatif (1–20, défaut 4); `category` et `source_file` sont facultatifs et peuvent être combinés. La catégorie doit correspondre exactement à l'une des cinq valeurs retournées par `/api/categories`.

Réponse `200` :

```json
{
  "question": "...",
  "reponse": "...",
  "sources": [
    {"fichier": "06_reglement_bibliotheque.txt", "categorie": "Règlements", "extrait": "..."}
  ],
  "filtre": "catégorie=Règlements + fichier=06_reglement_bibliotheque.txt",
  "temps_ms": 1234.5,
  "nb_chunks_trouves": 2
}
```

Erreurs : `400` (catégorie inconnue), `422` (question/corps invalide), `503` (pipeline RAG, ChromaDB, modèle local ou Ollama indisponible).

## `GET /api/categories` et `GET /api/documents`

- `/api/categories` renvoie `{"categories": {<catégorie>: {"nb_documents": ..., "documents": [...] }}, "total_documents": ...}`.
- `/api/documents` renvoie une liste d'objets `filename`, `categorie`, `date_ajout`, `type_original`, `chunks_count`. Le paramètre `?category=...` filtre la liste.
- Le dashboard doit utiliser ces routes pour afficher les statistiques documentaires, et `/api/health` pour l'état de l'API.

Les erreurs FastAPI de validation sont typiquement `{"detail": [...]}` (422); les erreurs de route utilisent `{"detail": "..."}`. Éviter de supposer qu'un `detail` est toujours une chaîne.
