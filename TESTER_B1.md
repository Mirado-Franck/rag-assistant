> **Installation d'abord** : si l'app ne se lance pas ou si tu as melange ancienne/nouvelle
> version, suis **`GUIDE_INSTALLATION_B1.md`** (etape 2), puis reviens ici pour le detail des tests.

# Tester ta part B1 — le mode d'emploi

Deux niveaux de test, à faire dans cet ordre :

| | Quoi | Durée | Ce que ça prouve |
|---|---|---|---|
| **1** | Tests automatiques (`tester_ui.bat`) | 1 min | Les 4 pages s'exécutent sans erreur, tous les clics/états fonctionnent → 54 vérifications |
| **2** | Checklist manuelle dans le navigateur | 10 min | L'expérience réelle : design, navigation, réponses, graphiques |

À la fin, tu as **trois preuves** à coller dans ton ticket : la sortie du test automatique, 3 captures d'écran, et la preuve « 100 % offline ».

---

## Étape 0 — Préparer (une seule fois)

Ouvre **Invite de commandes** (`Win + R` → `cmd` → Entrée), place-toi à la racine du projet :

```bat
cd C:\chemin\vers\le\projet
```

Installe les dépendances :

```bat
py -m pip install -r interface\requirements.txt
```

> Si `py` n'existe pas, utilise `python` à la place.
> Si tu as déjà Streamlit installé pour le projet, cette étape ne change rien.

Vérifie la structure (tu dois voir `app.py`, `nav.py`, `theme.py`, `data_mock.py`, `pages\`) :

```bat
dir interface
```

Place les deux fichiers `tester_ui.bat` et `lancer_ui.bat` **à la racine du projet** (à côté du dossier `interface\`).

---

## Étape 1 — Les tests automatiques (1 commande)

### La commande

```bat
verifier_b1.bat
```

(ou `python tests\test_ui_b1.py` pour ne lancer que les tests).
`verifier_b1.bat` fait les deux : controle de l'arborescence **puis** tests.
Il detecte aussi ton venv tout seul, et ne demande aucune politique PowerShell.

### Ce que tu dois voir

```
=== Tests interface DocuClassif AI — partie B1 (Jour 3) ===

✅ Accueil : la page s'exécute sans exception
✅ Accueil : titre et accroche présents
✅ Accueil : les 4 modules sont affichés
✅ Accueil : les 5 catégories sont affichées
✅ Accueil : badge 100 % offline visible
...
✅ Upload : état confirmé affiché
✅ Questions : les sources sont citées
✅ Dashboard : graphiques Altair présents (barres + courbe)
✅ Design : aucune ressource externe dans le CSS
✅ Offline : aucune dépendance réseau dans l'interface

============================================================
Résultat : 54/54 tests réussis — tout est vert 🎉
============================================================
```

### Comment ça marche (pour pouvoir l'expliquer au prof / au groupe)

`tests/test_ui_b1.py` utilise **`streamlit.testing.v1.AppTest`**, l'outil officiel de test de Streamlit :
il exécute réellement chaque page (comme un navigateur), puis **simule les clics et les saisies** :

- `button.click().run()` → clique sur « Charger un exemple », « Confirmer la catégorie », « Rejeter »…
- `chat_input.set_value("...").run()` → tape une question dans l'assistant
- `selectbox.set_value("Par catégorie").run()` → change le filtre
- `at.exception` → vérifie qu'aucune exception Python n'est remontée

**Pas besoin de navigateur, pas besoin d'Ollama, pas besoin du backend d'A2** : c'est autonome et reproductible en 6 secondes.

### Sauvegarder la preuve

```bat
python tests\test_ui_b1.py > preuve_tests_B1.txt 2>&1
```

Tu obtiens `preuve_tests_B1.txt` à joindre au ticket / à la PR.

---

## Étape 2 — Checklist manuelle (10 min, navigateur)

Lance l'interface :

```bat
python -m streamlit run interface\app.py
```

ou double-clic sur **`lancer_ui.bat`**. Ouvre ensuite <http://localhost:8501>.
Si Streamlit te demande ton e-mail au premier lancement, appuie sur **Entrée** (laisse vide) puis « **Always rerun** ».

Coche au fur et à mesure :

### A. Accueil (1 min)
- [ ] Le titre **DocuClassif AI** et la phrase d'accroche s'affichent.
- [ ] Les 2 badges « 100 % offline » et « Maquette · Jour 3 » sont visibles.
- [ ] Les **4 cartes** ont un contenu (titre + texte) et une **icône visible** à gauche.
- [ ] Les **5 catégories** apparaissent en pastilles.
- [ ] Le bloc **Démarrage rapide** (3 étapes) est présent.

### B. Sidebar (1 min)
- [ ] 4 entrées : Accueil, Upload, Questions, Tableau de bord — **sur une seule ligne**.
- [ ] L'entrée de la page courante est **surlignée** (fond blanc, bordure).
- [ ] En bas : badge **100 % offline** + bloc « Modèle / Moteur / Base / Mode ».

### C. Upload & Classification (3 min)
- [ ] Clique **Charger un exemple** → la catégorie **Guides pratiques** s'affiche à **80 %**, avec une barre verte.
- [ ] L'encart **Autres hypothèses** chiffre les catégories suivantes (20 %, 12 %, 7 %).
- [ ] Clique **Confirmer la catégorie** → bandeau vert « Classification confirmée » + « Document indexé dans ChromaDB (simulation) ».
- [ ] Clique **Analyser un autre document** → retour à l'état vide.
- [ ] **Cas confiance faible** : ne dépose aucun fichier, colle `note interne` dans le champ *Extrait de texte*, clique **Analyser le document** → la catégorie **Organisation** sort à **63 %** (confiance moyenne), avec l'encart « Confiance faible — vérifiez » et un message d'alerte.
- [ ] La liste **Corriger la catégorie** contient bien les 5 catégories ; en choisissant une autre, la mention « La validation enregistrera … » apparaît.
- [ ] Clique **Rejeter** → l'état vide revient.
- [ ] Le tableau **Classifications récentes** affiche 4 lignes.

### D. Questions & Réponses (2 min)
- [ ] Les filtres **Périmètre / Catégorie / Sources affichées / Session** sont alignés.
- [ ] Clique une suggestion (« Conditions pour obtenir une bourse ? ») → réponse structurée + expander **Sources · 3** avec fichier, catégorie, référence, score.
- [ ] Les métriques **Latence / Pertinence / Périmètre** s'affichent sous la réponse.
- [ ] Tape une question à la main dans le composer → elle apparaît dans la conversation, l'assistant répond.
- [ ] Passe le filtre sur **Par catégorie** → la ligne « Recherche limitée à … » change.
- [ ] Passe le filtre sur **Par fichier** → la liste des fichiers apparaît.
- [ ] Clique **Réinitialiser** → la conversation revient au message d'accueil.

### E. Tableau de bord (2 min)
- [ ] 4 indicateurs : Documents 15, Chunks 281, Questions 47, Classifications 12.
- [ ] Graphique en **barres** par catégorie (barres noires, pas de cyan).
- [ ] Encart **Volume par catégorie** avec barres horizontales.
- [ ] Courbe **Activité des 7 derniers jours**, jours dans l'ordre Lun → Dim.
- [ ] Tableau **Documents récemment ajoutés** (6 lignes) + bloc **Qualité du système**.
- [ ] Clique **Exporter (CSV)** → un fichier se télécharge.

### F. Le plus important : la preuve « 100 % offline »
- [ ] Coupe le Wi-Fi (ou débranche le câble), **rafraîchis avec `Ctrl + F5`**.
- [ ] Toute l'application continue de fonctionner (aucune police, icône ou image externe).
- [ ] Appuie sur `F12` → onglet **Network** → recharge : **aucune requête vers un domaine externe** (uniquement `localhost:8501`).

---

## Étape 3 — Ce que tu montres à l'équipe (3 min de démo)

Ordre de démo le plus convaincant :

1. **Accueil** → « voilà la maquette complète, 4 pages, design system commun ».
2. **Upload** → « Charger un exemple » → montrer la **jauge 80 %** → **confiance faible à 63 %** → **confirmer**.
   → Message : *« le classifieur de A1 se branchera ici en une ligne, le reste ne bouge pas »*.
3. **Questions** → une suggestion → réponse + **sources citées** → filtre par catégorie.
   → Message : *« il me faut de A2 : la réponse + les sources filtrées, format déjà défini »*.
4. **Dashboard** → graphiques + export CSV.
5. Terminer par **`preuve_tests_B1.txt`** : 54/54.

---

## Erreurs fréquentes (et la solution)

| Message | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'nav'` | Tu lances `streamlit run interface/pages/1_Upload.py` directement | Lance **toujours** `python -m streamlit run interface\app.py` |
| `ModuleNotFoundError: No module named 'streamlit'` | Dépendances pas installées | `py -m pip install -r interface\requirements.txt` |
| `Port 8501 is already in use` | Une ancienne instance tourne | Ferme l'autre fenêtre, ou `python -m streamlit run interface\app.py --server.port 8502` |
| `TypeError: button() got an unexpected keyword argument 'width'` | Streamlit trop ancien (< 1.33) | `py -m pip install -U "streamlit>=1.40"` |
| Les cartes sont vides / le texte ressemble à du code | Cache navigateur d'une ancienne version | `Ctrl + F5` |
| Le message `Please replace use_container_width with width` apparaît dans la console | Message **interne** de Streamlit (dépréciation), pas du projet | Ignorable — il n'apparaît pas dans l'interface |
| La page affiche `Page not found` | Tu as ouvert `/1_Upload` au lieu du chemin réel | Utilise la **sidebar**, pas l'URL |
| Le test automatique échoue sur `AppTest` | Streamlit < 1.28 | `py -m pip install -U "streamlit>=1.40"` |

---

## Commit / ticket

```bat
git add interface tests tester_ui.bat lancer_ui.bat TESTER_B1.md
git commit -m "Jour 3 : maquette UI complete + tests automatiques (54/54)"
```

Message type pour le ticket (Linear / Notion / Discord) :

> **B1 — Maquette UI complète (Jour 3) : prête pour revue**
> 4 pages Streamlit (Accueil, Upload & Classification, Questions, Dashboard) + design system centralisé.
> Autonome : aucune dépendance au backend A2 ni au classifieur A1 (données simulées).
> Tests : `python tests/test_ui_b1.py` → **54/54** (navigation, confiance haute/basse, confirmation, rejet, filtres RAG, sources, reset, graphiques, export CSV).
> Preuves jointes : `preuve_tests_B1.txt`, captures `apercus/`.
> Pour A1/A2 : les formats d'échange attendus (`/classify`, `/ask`) sont documentés dans `interface/README_B1.md` §6.
