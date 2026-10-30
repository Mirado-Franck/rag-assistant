# DocuClassif AI — Interface (Jour 3 · partie B1)

Maquette Streamlit **complète et autonome**, avec un design type ChatGPT :
fond blanc, sidebar gris clair, cartes à bordure fine, coins arrondis,
typographie système, icônes SVG inline (aucune ressource externe → **100 % offline**).

Aucune dépendance au backend de A2, au classifieur de A1 ni à ChromaDB :
tout est simulé dans `data_mock.py`.

---

## 1. Structure des fichiers

```
interface/
├── app.py                  → page d'accueil
├── nav.py                  → sidebar commune (navigation + badge offline)
├── theme.py                → design system (palette, icônes, composants HTML)
├── data_mock.py            → données + classifieur + RAG simulés (Jour 3)
├── assets/
│   └── style.css           → CSS complet du design system
├── .streamlit/
│   └── config.toml         → thème clair, toolbar masquée
└── pages/
    ├── 1_Upload.py         → Upload & Classification (confiance haute/basse + correction)
    ├── 2_Questions.py      → Assistant Q&R avec filtres (catégorie / fichier) + sources
    └── 3_Dashboard.py      → Statistiques, graphiques, qualité système
```

Aperçus PNG : dossier `../apercus/`.

## 2. Lancer

```bash
pip install -r interface/requirements.txt
streamlit run interface/app.py
```

> Le dossier de lancement n'a pas d'importance : les imports locaux
> (`import nav`, `import theme`) fonctionnent car Streamlit ajoute le dossier
> du script au `sys.path`.

Au premier lancement, Streamlit peut afficher un écran d'accueil : cliquez
sur **« Always rerun »** si demandé.

## 3. Correspondance avec le plan (checklist B1)

| Étape du plan | État | Où |
|---|---|---|
| B1.1 Architecture multi-pages | ✅ | `app.py` + `pages/` + `nav.py` (sidebar commune) |
| B1.2 Page d'accueil | ✅ | `app.py` (4 modules, 5 catégories, démarrage rapide) |
| B1.3 Upload & Classification | ✅ | `pages/1_Upload.py` |
| B1.4 Questions & Réponses | ✅ | `pages/2_Questions.py` |
| B1.5 Dashboard | ✅ | `pages/3_Dashboard.py` |
| B1.6 Lancer et tester | ✅ | voir §5 |
| Navigation multi-pages fonctionnelle | ✅ | boutons sidebar avec état actif |
| Cas « confiance haute » + « confiance basse » | ✅ | `confidence_meter()` + encart alternatives |
| RAG simulé avec filtres (catégorie + fichier) | ✅ | sélecteurs Périmètre / Catégorie / Fichier |
| Sources affichées | ✅ | expander « Sources · n » avec fichier, catégorie, référence, score |
| Dashboard avec graphiques | ✅ | barres (Altair) + courbe d'activité + tableau |
| Design professionnel | ✅ | `theme.py` + `assets/style.css` |
| Badge « 100 % OFFLINE » | ✅ | sidebar, sous « Système » |

## 4. Design system (à réutiliser les jours suivants)

Tout passe par `theme.py` : ne recopiez jamais de CSS dans une page.

```python
import nav, theme

nav.setup("questions", "Questions")          # set_page_config + CSS + sidebar
theme.page_header("Titre", "Sous-titre", "Étape 2")
theme.section("Bloc", "hint à droite")
theme.card_grid([("Titre", "Corps", "chat")], per_row=2)
theme.stat_cards([{"label": "Documents", "value": 15, "delta": "+3 cette semaine"}])
theme.chips([("Règlements", "· Lois, décrets", "file")])
theme.badge("100 % offline")                  # badge() renvoie une string HTML
theme.button("Valider", primary=True, full=True)   # compatible Streamlit ≥ 1.30
theme.dataframe(rows, hide_index=True)             # compatible Streamlit ≥ 1.30
theme.chart(fig)                                   # Altair pleine largeur
theme.divider()
```

Palette (dans `assets/style.css`) :

| Rôle | Valeur |
|---|---|
| Encre / texte | `#0d0d0d` |
| Texte secondaire | `#5d5d6b` |
| Bordures | `#e6e6e6` |
| Fond doux / sidebar | `#f9f9f9` |
| Succès / confiance | `#10a37f` |
| Alerte / confiance moyenne | `#c98a00` |

Deux pièges déjà résolus, à ne pas réintroduire :

1. **Pas de `<svg>` inline** : le sanitizer de `st.html` supprime les balises
   `<svg>` injectées en HTML brut. `theme.icon()` renvoie donc une image
   `data:image/svg+xml;base64,…`, ce qui fonctionne partout et reste offline.
2. **Pas de `st.html()` avec un bloc indenté multi-lignes** : Streamlit le
   traite comme du Markdown et affiche le code. `theme.html()` aplatit les
   lignes et retombe sur `st.markdown(..., unsafe_allow_html=True)` si besoin.

## 5. Tests de validation (Jour 3)

### 5.1 Automatique (recommandé, 1 commande)

```bash
python tests/test_ui_b1.py        # 54 vérifications, ~6 s, sans navigateur
```

Le script utilise `streamlit.testing.v1.AppTest` : il exécute réellement les 4 pages,
simule les clics (Charger un exemple, Confirmer, Rejeter, Réinitialiser), les saisies
(chat_input) et les filtres (selectbox), puis vérifie qu'aucune exception n'est levée.
Guide détaillé (Windows, démo, dépannage) : `TESTER_B1.md` à la racine.

### 5.2 Manuel (10 min, dans le navigateur)

À dérouler avant de valider la part B1 :

1. Accueil : les 4 modules, les 5 catégories et le démarrage rapide s'affichent.
2. Sidebar : les 4 entrées naviguent et l'entrée active est surlignée.
3. Sidebar : le badge « 100 % offline » et le bloc Système sont visibles.
4. Upload : « Charger un exemple » affiche *Guides pratiques* à 80 %.
5. Upload : « Confirmer la catégorie » affiche l'état confirmé + l'indexation simulée.
6. Upload : « Rejeter » et « Analyser un autre document » réinitialisent.
7. Upload : la liste de correction propose les 5 catégories.
8. Questions : un filtre par catégorie limite la recherche (libellé sous les filtres).
9. Questions : une suggestion ou une question tapée déclenche la réponse + les sources.
10. Questions : « Réinitialiser » vide la conversation.
11. Dashboard : 4 indicateurs, graphique en barres, courbe d'activité, tableau.
12. Dashboard : l'export CSV se télécharge.
13. Aucune exception affichée dans l'UI, aucune requête réseau externe.

## 6. Basculer sur les vrais modules (Jours 4–5)

Une seule fonction à remplacer par page, pour ne pas toucher au design :

```python
# pages/1_Upload.py  — Jour 4
# avant
resultat = predict_category(nom, texte)
# après
import requests
resultat = requests.post("http://localhost:8000/classify",
                         json={"filename": nom, "text": texte}, timeout=60).json()

# pages/2_Questions.py — Jour 5
# avant
resultat = answer_question(question, scope=scope, n_sources=n_sources)
# après
resultat = requests.post("http://localhost:8000/ask",
                         json={"question": question, "filtre_categorie": scope,
                               "n_sources": n_sources}, timeout=120).json()
```

Le contrat de données à exiger de A2 (format déjà utilisé par la maquette) :

```json
// POST /classify
{"categorie": "Guides pratiques", "confiance": 0.80,
 "alternatives": [{"label": "Règlements", "score": 0.20}],
 "chunks_estimes": 7, "fiable": true}

// POST /ask
{"content": "…", "sources": [{"fichier": "…", "categorie": "…",
 "ref": "Page 3, §2", "score": 0.92}],
 "meta": {"latence": "1.7 s", "pertinence": "71 %", "filtre": "Tous"}}
```

Les pages Dashboard liront alors les agrégats réels (compteurs ChromaDB + logs API)
à la place des valeurs de `data_mock.STATS`.

## 7. Commit Git

```bash
git add interface/ && git commit -m "Jour 3 : maquette UI complète (design system + 4 pages)"
```
