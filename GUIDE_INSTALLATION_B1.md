# GUIDE D'INSTALLATION - Partie B1 (Jour 3)

> Ecrit pour PowerShell sous Windows, projet `rag-assistant`.
> Suis les etapes DANS L'ORDRE. Ne saute pas l'etape 2 : c'est elle qui corrige
> ton erreur actuelle (`Could not find page: pages/Upload.py`).

---

## Ce qui s'est passe sur ta machine

Ton dossier `interface/` contient un **melange de deux versions** :

| Fichier | Etat |
|---|---|
| `interface/app.py` | ANCIENNE version (celle du plan : `st.page_link("pages/Upload.py")`, emojis) |
| `interface/pages/1_Upload.py`, `2_Questions.py`, `3_Dashboard.py` | NOUVELLE version (la mienne) |

L'ancien `app.py` cherche `pages/Upload.py`, qui n'existe plus (les pages
s'appellent maintenant `1_Upload.py`, `2_Questions.py`, `3_Dashboard.py`).
D'ou le message :

```
StreamlitPageNotFoundError: Could not find page: `pages/Upload.py`
```

**Cause racine : tous les fichiers de `interface/` doivent venir de la MEME version.**
On ne peut pas garder l'ancien `app.py` avec les nouvelles pages.

Bonne nouvelle : les 3 pages, le CSS et les tests fonctionnent deja chez toi
(46 tests verts). Il ne reste qu'a remplacer `app.py` et supprimer les restes.

---

## Etape 1 - Se placer dans le projet et activer le venv

```powershell
cd "C:\Users\WINDOWS 11\rag-assistant"
.\venv\Scripts\Activate.ps1
```

Ton invite doit commencer par `(venv)`.

> Si PowerShell refuse (`execution of scripts is disabled`) :
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> puis relance `.\venv\Scripts\Activate.ps1`.

Verifie que Streamlit est la :

```powershell
python -c "import streamlit; print(streamlit.__version__)"
```

Tu dois voir une version **>= 1.40** (ex. `1.66.1`). Sinon :

```powershell
python -m pip install -r interface\requirements.txt
```

---

## Etape 2 - Repartir d'un dossier `interface/` propre

### 2.1 Sauvegarder l'ancien dossier (au cas ou)

```powershell
Rename-Item interface interface_OLD
```

(Ca renomme, ca ne supprime rien. Le dossier `interface_OLD` ne genera plus
Streamlit, il suffit de l'ignorer. Tu pourras le supprimer plus tard.)

### 2.2 Extraire la nouvelle archive a la racine du projet

Telecharge **`interface_B1.zip`** (celui de ce message, ~40 Ko) puis :

```powershell
Expand-Archive -Path .\interface_B1.zip -DestinationPath . -Force
```

Tu dois obtenir exactement :

```
rag-assistant\
├── interface\
│   ├── app.py                  <- NOUVEAU (l'accueil)
│   ├── nav.py
│   ├── theme.py
│   ├── data_mock.py
│   ├── requirements.txt
│   ├── README_B1.md
│   ├── assets\style.css
│   ├── .streamlit\config.toml
│   └── pages\
│       ├── 1_Upload.py
│       ├── 2_Questions.py
│       └── 3_Dashboard.py
├── tests\
│   └── test_ui_b1.py
├── verifier_b1.ps1
├── lancer_ui.bat
├── GUIDE_INSTALLATION_B1.md    <- ce fichier
└── TESTER_B1.md
```

### 2.3 Verifier l'arborescence avant de lancer quoi que ce soit

```powershell
.\verifier_b1.ps1
```

Ce script controle la presence de chaque fichier, signale les **restes de
l'ancienne version**, puis lance les tests automatiques.
Tu dois terminer par :

```
INSTALLATION B1 : OK
TESTS : 61/61 reussis
```

> Si PowerShell bloque l'execution du script, lance-le autrement :
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\verifier_b1.ps1
> ```

---

## Etape 3 - Lancer les tests automatiques seuls

```powershell
python tests\test_ui_b1.py
```

Attendu :

```
=== Tests interface DocuClassif AI - partie B1 (Jour 3) ===

OK Structure : les 3 pages du plan existent
OK Structure : aucun fichier de page en trop (restes de l'ancienne version)
OK Structure : app.py est la nouvelle version (pas de st.page_link)
OK Structure : toutes les cibles de navigation existent
OK Accueil : la page s'execute sans exception
...
============================================================
Resultat : 61/61 tests reussis - tout est vert
============================================================
```

(Le compte peut varier de 1-2 selon la version de Streamlit : ce qui compte est
**0 echec**.)

### Garder la preuve pour ton ticket

```powershell
python tests\test_ui_b1.py 2>&1 | Tee-Object -FilePath preuve_tests_B1.txt
```

### Les messages a IGNORER (ils viennent de Streamlit, pas de ton projet)

```
missing ScriptRunContext! This warning can be ignored when running in bare mode.
Please replace `use_container_width` with `width`... will be removed after 2025-12-31
```

Aucun des deux n'affecte l'application. Ils n'apparaissent pas dans le navigateur.

---

## Etape 4 - Lancer l'interface

```powershell
python -m streamlit run interface\app.py
```

Puis ouvre **http://localhost:8501**

- Si Streamlit demande un e-mail : appuie sur **Entree** (laisse vide).
- Si tu vois « Always rerun » : clique dessus.
- Ne lance **jamais** `python -m streamlit run interface\pages\1_Upload.py`
  (ca marcherait maintenant, mais la navigation resterait bloquee sur cette page).

---

## Etape 5 - Checklist manuelle (10 min, dans le navigateur)

### A. Accueil
- [ ] Titre **DocuClassif AI** + phrase d'accroche.
- [ ] Badges **100 % offline** et **Maquette · Jour 3**.
- [ ] **4 cartes** avec titre, texte et icone a gauche (pas de cartes vides).
- [ ] **5 categories** en pastilles.
- [ ] Bloc **Demarrage rapide** (3 etapes).

### B. Sidebar
- [ ] 4 entrees : Accueil, Upload, Questions, Tableau de bord (sur une ligne).
- [ ] L'entree courante est surlignee.
- [ ] Badge **100 % offline** + bloc Modele / Moteur / Base / Mode.

### C. Upload & Classification
- [ ] **Charger un exemple** -> *Guides pratiques* a **80 %**, barre verte.
- [ ] Encart **Autres hypotheses** (20 %, 12 %, 7 %).
- [ ] **Confirmer la categorie** -> bandeau « Classification confirmee ».
- [ ] **Analyser un autre document** -> retour a l'etat vide.
- [ ] **Confiance faible** : aucun fichier + coller `note interne` dans *Extrait de texte*
      -> *Organisation* a **63 %** + encart « Confiance faible — verifiez ».
- [ ] La liste de correction contient bien les **5 categories**.
- [ ] **Rejeter** -> etat vide.
- [ ] Tableau **Classifications recentes** : 4 lignes.

### D. Questions & Reponses
- [ ] Filtres Perimetre / Categorie / Sources / Session alignes.
- [ ] Une suggestion -> reponse + expander **Sources · 3** (fichier, categorie, reference, score).
- [ ] Metriques **Latence / Pertinence / Perimetre** sous la reponse.
- [ ] Question tapee a la main -> elle apparait, l'assistant repond.
- [ ] Filtre **Par categorie** -> la ligne « Recherche limitee a … » change.
- [ ] Filtre **Par fichier** -> la liste des fichiers apparait.
- [ ] **Reinitialiser** -> retour au message d'accueil.

### E. Tableau de bord
- [ ] 4 indicateurs : Documents 15, Chunks 281, Questions 47, Classifications 12.
- [ ] Barres noires par categorie (plus de cyan).
- [ ] Encart **Volume par categorie**.
- [ ] Courbe **Activite des 7 derniers jours**, jours dans l'ordre Lun -> Dim.
- [ ] Tableau **Documents recemment ajoutes** + bloc **Qualite du systeme**.
- [ ] **Exporter (CSV)** telecharge un fichier.

### F. La preuve qui compte : 100 % offline
- [ ] Coupe le Wi-Fi.
- [ ] `Ctrl + F5` : toute l'application fonctionne encore.
- [ ] `F12` -> onglet **Network** -> recharge : aucune requete vers un domaine externe
      (uniquement `localhost:8501`).

---

## Etape 6 - Commit et message pour le ticket

```powershell
git add interface tests verifier_b1.ps1 lancer_ui.bat GUIDE_INSTALLATION_B1.md TESTER_B1.md
git commit -m "Jour 3 : maquette UI complete (design system) + tests automatiques"
```

Message pret a coller (Linear / Notion / Discord) :

> **B1 — Maquette UI complete (Jour 3) : prete pour revue**
> 4 pages Streamlit (Accueil, Upload & Classification, Questions, Dashboard) + design system centralise.
> Autonome : aucune dependance au backend A2 ni au classifieur A1 (donnees simulees).
> Tests : `python tests\test_ui_b1.py` -> **61/61** (navigation, confiance haute/basse, confirmation,
> rejet, filtres RAG, sources, reset, graphiques, export CSV, offline).
> Preuves jointes : `preuve_tests_B1.txt` + captures `apercus/`.
> Pour A1/A2 : formats d'echange attendus (`/classify`, `/ask`) documentes dans `interface/README_B1.md` §6.

---

## Depannage express

| Message | Cause | Solution |
|---|---|---|
| `Could not find page: pages/Upload.py` | ancien `app.py` | refais l'etape 2 |
| `ModuleNotFoundError: No module named 'nav'` | lance depuis un mauvais dossier, ou fichier manquant | `cd` a la racine, verifie `dir interface` |
| `ModuleNotFoundError: No module named 'streamlit'` | venv non active | `.\venv\Scripts\Activate.ps1` |
| `StreamlitAPIException: set_page_config ... can only be called once` | deux `app.py` melanges | refais l'etape 2 |
| `Port 8501 is already in use` | instance deja lancee | ferme l'autre fenetre, ou `--server.port 8502` |
| `TypeError: ... unexpected keyword argument 'width'` | Streamlit < 1.33 | `python -m pip install -U "streamlit>=1.40"` |
| Cartes vides / texte en style code | cache de l'ancienne version | `Ctrl + F5` |
| Le script `.ps1` ne se lance pas | ExecutionPolicy | `powershell -ExecutionPolicy Bypass -File .\verifier_b1.ps1` |

---

## Ce que tu n'as plus besoin de faire

- Ne modifie **aucun** fichier a la main dans `interface/`.
- Ne copie **pas** de code depuis la conversation : tout est deja dans l'archive.
- Le dossier `interface_OLD` peut etre supprime une fois que tout est vert :
  ```powershell
  Remove-Item -Recurse -Force interface_OLD
  ```
