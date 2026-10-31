# DocuRAG — Interface (partie B1, Jour 6)

Interface Streamlit branchée sur l'API FastAPI locale (`src/api/main.py`).
Design sobre (fond blanc, cartes fines, palette par catégorie), icônes SVG inline.
Aucune ressource externe : l'interface fonctionne sans internet.

Les données ne sont plus simulées : tout ce qui s'affiche vient de l'API, ou
affiche un message d'erreur si l'API ne répond pas.

---

## 1. Structure

```
interface/
├── app.py                  → accueil (état de l'API, catégories, démarrage rapide)
├── nav.py                  → sidebar commune (navigation, état réel de l'API)
├── theme.py                → design system (palette, icônes, composants HTML)
├── config.py               → constantes : catégories, seuils de confiance, URL de l'API
├── api_client.py           → seul module qui appelle l'API (requests, timeouts, messages d'erreur)
├── assets/style.css        → CSS du design system
├── .streamlit/config.toml  → thème clair, toolbar masquée
└── views/                  → pages (chargées par st.navigation, pas par le dossier pages/)
    ├── 1_Upload.py         → Upload & Classification en 4 étapes
    ├── 2_Questions.py      → Questions & Réponses (chat, filtres, sources)
    └── 3_Dashboard.py      → Tableau de bord (statistiques réelles)
```

## 2. Lancer

Dans cet ordre, depuis la racine du projet :

```bash
# 1. Backend (Ollama doit tourner pour les vraies réponses)
uvicorn src.api.main:app --host 127.0.0.1 --port 8000

# 2. Interface
pip install -r interface/requirements.txt
streamlit run interface/app.py
```

L'adresse de l'API se règle avec la variable `DOCUCLASSIF_API_URL`
(par défaut `http://127.0.0.1:8000`).

Si le backend est arrêté, l'interface reste ouverte : la sidebar affiche
« API hors ligne » et chaque page affiche une erreur lisible au lieu de planter.

## 3. Upload & Classification (4 étapes)

| Étape | Ce qui se passe | Route API |
|---|---|---|
| 1. Dépôt | Fichier PDF / DOCX / TXT, ou texte collé, ou « Charger un exemple » | — |
| 2. Extraction | Aperçu du texte extrait | `POST /api/upload` |
| 3. Proposition | Catégorie proposée selon la confiance (voir ci-dessous) | `POST /api/upload` |
| 4. Confirmation | Indexation du document, nombre de chunks | `POST /api/confirm` |

Trois cas selon le score de confiance (seuils dans `config.py`) :

| Confiance | Affichage | Action |
|---|---|---|
| > 80 % | Catégorie proposée, confiance élevée | Confirmer, ou Changer de catégorie |
| 60 % à 80 % | Alternatives avec leurs probabilités | Choisir dans la liste, puis valider |
| < 60 % | « Confiance trop faible », aucune catégorie préchoisie | Choix manuel obligatoire (bouton inactif tant que rien n'est choisi) |

Un document confirmé mais non indexé (ChromaDB ou embeddings indisponibles) est
signalé comme tel. Une classification de secours (modèle local injoignable) est
signalée comme « indicative ».

## 4. Questions & Réponses

- Chat avec historique pendant la session ; « Réinitialiser » vide la conversation.
- Périmètre : tous les documents, une catégorie, ou un fichier confirmé (`POST /api/query`).
- Nombre de sources affichées : 1 à 20 (par défaut 4).
- Chaque réponse affiche ses sources (fichier, catégorie, extrait) et la latence.
- Si le moteur RAG n'est pas disponible, la réponse est signalée comme « mode dégradé ».
- Si l'API tombe, l'erreur s'affiche dans la conversation et la saisie reste disponible.

## 5. Tableau de bord

Lit `/api/health`, `/api/categories` et `/api/documents` :

- documents, chunks indexés, documents non indexés, catégories couvertes ;
- chunks par catégorie (graphique) et documents par catégorie ;
- documents récemment ajoutés ; export CSV de la liste ;
- bloc « qualité du système » (modèles, état de l'API).

L'API n'expose ni historique de questions ni historique de classifications :
ces indicateurs ne sont pas affichés.

## 6. Tests

```bash
python tests/test_ui_b1.py
```

Le script lance les pages Streamlit avec un faux client API (aucun backend ni
Ollama requis) et vérifie : les trois cas de confiance, les étapes de l'upload,
le chat et ses filtres, les pannes de l'API, les chiffres du tableau de bord,
et l'absence de ressource externe. Le script affiche le nombre de tests réussis et un code de sortie non nul en cas d'échec.

Le parcours complet dans le navigateur (upload → confirmation → question → réponse)
se fait contre le vrai backend ; voir `TESTER_B1.md`.

## 7. Contrat avec l'API

Les routes et formats sont décrits dans `docs/api_contract.md`. Les libellés de
catégories de `config.py` doivent rester identiques à ceux de l'API (un test le vérifie).
