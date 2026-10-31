"""
test_ui_b1.py - Tests automatiques de l'interface (partie B1, Jour 6).

Aucun navigateur ni backend necessaire : on utilise streamlit.testing.v1.AppTest,
qui execute reellement les pages Streamlit et simule les clics / saisies.
Les appels a l'API sont remplaces par un faux client (FakeApi) : on teste ainsi
le comportement de l'interface pour les 3 cas de confiance, les pannes de l'API,
les filtres et les chiffres du tableau de bord.

Lancement (depuis la racine du projet) :

    python tests/test_ui_b1.py

Sortie : une ligne [OK] / [ECHEC] par test, un resume, et un code de sortie
non nul si un test echoue.

Fichier volontairement 100% ASCII (ni accents, ni emoji) : la console Windows
est souvent en cp1252. Les comparaisons avec le texte de l'interface sont
faites sans accents (fonction norm).

Dependance : streamlit >= 1.40 (AppTest). Rien d'autre.
"""

from __future__ import annotations

import logging
import re
import sys
import traceback
import unicodedata
from pathlib import Path

# --- 1. Sortie console sure (Windows cp1252 / cp850) -----------------------
for _flux in (sys.stdout, sys.stderr):
    try:
        _flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def norm(texte) -> str:
    """Minuscules + sans accents : permet de comparer du texte non-ASCII."""
    t = str(texte)
    try:
        t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    except Exception:
        t = t.encode("ascii", "replace").decode("ascii")
    return t.lower()


def say(*morceaux) -> None:
    """print() qui ne peut jamais lever UnicodeEncodeError."""
    try:
        print(*morceaux)
    except UnicodeEncodeError:
        print(*[norm(m) for m in morceaux])


# --- 2. Imports ------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
INTERFACE = ROOT / "interface"
sys.path.insert(0, str(INTERFACE))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402  (module partage avec les pages executees par AppTest)
import nav  # noqa: E402
from config import CATEGORY_LABELS, DEFAULT_API_URL  # noqa: E402

for _nom in (
    "streamlit",
    "streamlit.deprecation_util",
    "streamlit.runtime.scriptrunner_utils.script_run_context",
):
    logging.getLogger(_nom).setLevel(logging.CRITICAL)

APP = str(INTERFACE / "app.py")
PAGE_UPLOAD = str(INTERFACE / "pages" / "1_Upload.py")
PAGE_QUESTIONS = str(INTERFACE / "pages" / "2_Questions.py")
PAGE_DASHBOARD = str(INTERFACE / "pages" / "3_Dashboard.py")
PAGES_ATTENDUES = ["1_Upload.py", "2_Questions.py", "3_Dashboard.py"]

TIMEOUT = 60
results: list[tuple[bool, str, str]] = []


# --- 3. Faux client API ----------------------------------------------------
class FakeApi:
    """Remplace les fonctions de api_client. Enregistre les appels reçus."""

    def __init__(self) -> None:
        self.down = False
        self.calls: list[tuple] = []
        self.upload_resp: dict = {}
        self.confirm_error: str | None = None
        self.confirm_resp: dict = {}
        self.query_resp: dict = {}
        self.documents_list: list[dict] = []
        self.categories_resp: dict = {}

    def _check(self, nom: str) -> None:
        self.calls.append((nom,))
        if self.down:
            raise api_client.ApiError(api_client.MESSAGE_API_DOWN)

    def health(self):
        self._check("health")
        return {"status": "ok", "modele_llm": "llama3.2", "modele_embedding": "minilm",
                "nb_documents": len(self.documents_list), "nb_chunks": 200, "categories": {}}

    def categories(self):
        self._check("categories")
        return {"categories": self.categories_resp, "total_documents": len(self.documents_list)}

    def documents(self, category=None):
        self._check("documents")
        return list(self.documents_list)

    def upload(self, filename, content):
        self._check("upload")
        self.calls.append(("upload_args", filename, len(content)))
        return dict(self.upload_resp)

    def confirm(self, file_id, categorie):
        self._check("confirm")
        self.calls.append(("confirm_args", file_id, categorie))
        if self.confirm_error:
            raise api_client.ApiError(self.confirm_error, 404)
        return dict(self.confirm_resp)

    def query(self, question, n_results=4, category=None, source_file=None):
        self._check("query")
        self.calls.append(("query_args", question, n_results, category, source_file))
        return dict(self.query_resp)

    def args(self, nom: str) -> list[tuple]:
        return [c[1:] for c in self.calls if c[0] == nom]


FAKE = FakeApi()


def install_fake() -> FakeApi:
    """Branche le faux client sur api_client (les pages l'appellent par attribut)."""
    for nom in ("health", "categories", "documents", "upload", "confirm", "query"):
        setattr(api_client, nom, getattr(FAKE, nom))
    nav.api_state.clear()
    return FAKE


def scenario(**kwargs) -> FakeApi:
    """Remet le faux serveur dans un etat connu."""
    FAKE.__init__()
    FAKE.documents_list = [
        {"filename": "01_reglement_interieur.txt", "categorie": "Règlements",
         "date_ajout": "2026-10-27", "type_original": "PDF", "chunks_count": 30},
        {"filename": "02_guide_bourses.txt", "categorie": "Guides pratiques",
         "date_ajout": "2026-10-28", "type_original": "PDF", "chunks_count": 17},
        {"filename": "19_formulaire_bourse.txt", "categorie": "Formulaires & documents ponctuels",
         "date_ajout": "2026-10-29", "type_original": "DOCX", "chunks_count": 0},
    ]
    FAKE.categories_resp = {
        "Règlements": {"nb_documents": 1, "documents": ["01_reglement_interieur.txt"]},
        "Guides pratiques": {"nb_documents": 1, "documents": ["02_guide_bourses.txt"]},
        "Procédures": {"nb_documents": 0, "documents": []},
        "Organisation & plannings": {"nb_documents": 0, "documents": []},
        "Formulaires & documents ponctuels": {"nb_documents": 1, "documents": ["19_formulaire_bourse.txt"]},
    }
    FAKE.down = bool(kwargs.get("down", False))
    install_fake()
    return FAKE


def upload_resp(confiance: float, categorie: str = "Guides pratiques", alternatives=None) -> dict:
    return {
        "categorie": categorie,
        "confiance": confiance,
        "justification": "Justification de test.",
        "alternatives": alternatives or [],
        "needs_confirmation": confiance <= 0.8,
        "file_id": "a1b2c3d4",
        "filename": "guide_test.txt",
        "text_preview": "GUIDE DES BOURSES ... apercu du texte extrait.",
    }


# --- 4. Outils -------------------------------------------------------------
def run(path: str) -> AppTest:
    at = AppTest.from_file(path, default_timeout=TIMEOUT)
    at.run()
    return at


def page_text(at: AppTest) -> str:
    """Texte visible d'une page, sans accents (voir norm)."""
    chunks = []
    for groupe in ("html", "markdown", "caption", "title", "header", "subheader", "warning", "info"):
        chunks += [str(el.value) for el in at.get(groupe)]
    chunks += [str(b.label) for b in at.button]
    chunks += [str(c.label) for c in at.selectbox]
    chunks += [str(e.label) for e in at.expander]
    chunks += [str(e.value) for e in at.error]
    return norm(" ".join(chunks))


def set_option(at: AppTest, index: int, cible: str):
    """Selectionne l'option du selectbox dont le libelle correspond (sans accents)."""
    options = list(at.selectbox[index].options)
    reel = next((o for o in options if norm(o) == norm(cible)), None)
    if reel is None:
        reel = next((o for o in options if norm(cible) in norm(o)), options[0])
    at.selectbox[index].set_value(reel).run()
    return reel


def button(at: AppTest, label: str):
    """Retrouve un bouton par son libelle, accents et casse ignores."""
    return next((b for b in at.button if norm(b.label) == norm(label)), None)


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((bool(condition), name, detail))
    ligne = ("[OK]    " if condition else "[ECHEC] ") + name
    if detail and not condition:
        ligne += "  ->  " + str(detail)
    say(ligne)


AIDE = {
    "Could not find page": "lance streamlit depuis la racine : streamlit run interface/app.py",
    "No module named 'nav'": "verifie que nav.py, theme.py et config.py sont dans interface/.",
    "No module named 'streamlit'": "active le venv et installe interface/requirements.txt.",
    "No module named 'api_client'": "api_client.py manque dans interface/ : verifie le depot.",
}


def no_exception(at: AppTest, name: str) -> bool:
    if at.exception:
        detail = "; ".join(e.message for e in at.exception)
        for cle, aide in AIDE.items():
            if cle in detail:
                detail += "  ->  " + aide
        check(name, False, detail)
        return False
    check(name, True)
    return True


# --- 5. Structure et contrats ---------------------------------------------
def test_structure() -> None:
    pages_dir = INTERFACE / "pages"
    check("Structure : les 3 pages du plan existent",
          all((pages_dir / nom).exists() for nom in PAGES_ATTENDUES),
          str(sorted(p.name for p in pages_dir.glob("*.py"))))
    restes = [p.name for p in pages_dir.glob("*.py") if p.name not in PAGES_ATTENDUES]
    check("Structure : aucun fichier de page en trop", not restes, "a supprimer : " + str(restes))
    check("Structure : data_mock.py supprime (plus de donnees simulees)",
          not (INTERFACE / "data_mock.py").exists())
    check("Structure : modules api_client.py et config.py presents",
          (INTERFACE / "api_client.py").exists() and (INTERFACE / "config.py").exists())

    manquantes = [cible for _, _, _, cible in nav.NAV if not (INTERFACE / cible).exists()]
    check("Structure : toutes les cibles de navigation existent", not manquantes, str(manquantes))

    api_src = (ROOT / "src" / "api" / "main.py").read_text(encoding="utf-8", errors="replace")
    bloc = re.search(r"CATEGORIES\s*=\s*\[(.*?)\]", api_src, re.S)
    categories_api = re.findall(r'"([^"]+)"', bloc.group(1)) if bloc else []
    check("Contrat : les categories de config.py sont identiques a celles de l'API",
          categories_api == CATEGORY_LABELS, str(categories_api))


def test_api_client_unit() -> None:
    bande = api_client.confidence_band
    check("Confiance : 0.81 -> haute", bande(0.81) == "haute")
    check("Confiance : 0.80 exactement -> moyenne (seuil strict)", bande(0.80) == "moyenne")
    check("Confiance : 0.60 -> moyenne", bande(0.60) == "moyenne")
    check("Confiance : 0.59 -> faible", bande(0.59) == "faible")
    check("Confiance : 0.0 -> faible", bande(0.0) == "faible")

    alts = api_client.normalize_alternatives([
        {"categorie": "Procédures", "probabilite": 0.15},
        {"categorie": "Règlements", "score": 0.4},
        {"pas": "valide"},
    ])
    check("Alternatives : triees par probabilite, cles tolerees",
          [a["categorie"] for a in alts] == ["Règlements", "Procédures"], str(alts))

    original = api_client.API_URL
    api_client.API_URL = "http://127.0.0.1:9"  # port ferme : connexion refusee
    try:
        api_client.health()
        check("Erreur reseau : ApiError levee (pas d'exception brute)", False, "aucune erreur")
    except api_client.ApiError as exc:
        check("Erreur reseau : message 'API indisponible' lisible",
              exc.message == api_client.MESSAGE_API_DOWN, exc.message)
    except Exception as exc:  # noqa: BLE001
        check("Erreur reseau : ApiError levee (pas d'exception brute)", False, repr(exc))
    finally:
        api_client.API_URL = original

    check("Securite : l'API par defaut est une adresse locale",
          re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", DEFAULT_API_URL) is not None,
          DEFAULT_API_URL)


# --- 6. Accueil -----------------------------------------------------------
def test_accueil() -> None:
    scenario()
    at = run(APP)
    if not no_exception(at, "Accueil : la page s'execute sans exception (API en ligne)"):
        return
    txt = page_text(at)
    check("Accueil : badge 100 % offline visible quand l'API repond", "100 % offline" in txt)
    check("Accueil : nombre de documents lu depuis l'API", "3 document(s)" in txt)
    check("Accueil : les 5 categories sont affichees",
          all(c in txt for c in ["reglements", "guides pratiques", "procedures",
                                 "organisation", "formulaires"]))
    labels = [b.label for b in at.button]
    check("Sidebar : 4 entrees de navigation",
          all(l in labels for l in ["Accueil", "Upload", "Questions", "Tableau de bord"]), str(labels))

    scenario(down=True)
    at = run(APP)
    if no_exception(at, "Accueil : la page s'execute sans exception (API arretee)"):
        txt = page_text(at)
        check("Accueil : badge 'API hors ligne' affiche quand l'API est arretee",
              "api hors ligne" in txt)
        check("Accueil : message d'erreur lisible affiche", "lancez le backend" in txt)


# --- 7. Upload : les 4 etapes et les 3 cas de confiance -------------------
def _depot(at: AppTest, texte: str) -> None:
    at.text_area[0].set_value(texte)
    button(at, "Analyser le document").click().run()


def test_upload_cas_confiance_haute() -> None:
    fake = scenario()
    fake.upload_resp = upload_resp(0.93, "Guides pratiques")
    fake.confirm_resp = {"status": "success", "message": "Document confirme et indexe.",
                         "file_id": "a1b2c3d4", "source_file": "a1b2c3d4_guide_test.txt",
                         "categorie": "Guides pratiques", "indexe": True, "nb_chunks": 12}
    at = run(PAGE_UPLOAD)
    if not no_exception(at, "Upload : la page s'execute sans exception"):
        return
    check("Upload : etape 1 (depot) au demarrage", "depot" in page_text(at) and "extraction" in page_text(at))

    _depot(at, "Texte de test suffisamment long pour etre classe par le modele local.")
    no_exception(at, "Upload : l'analyse s'execute sans exception")
    check("Upload : etape 2 (extraction) apres l'analyse", "texte extrait" in page_text(at))
    check("Upload : l'upload envoie le texte saisi sous forme de fichier",
          any(a[0] == "extrait_saisi.txt" for a in fake.args("upload_args")))

    button(at, "Continuer vers la proposition").click().run()
    txt = page_text(at)
    check("Upload : confiance haute -> 'Confiance elevee' affichee", "confiance elevee" in txt)
    check("Upload : confiance haute -> categorie proposee affichee", "guides pratiques" in txt)
    check("Upload : confiance haute -> boutons Confirmer et Changer presents",
          button(at, "Confirmer la catégorie") is not None and button(at, "Changer de catégorie") is not None)

    button(at, "Confirmer la catégorie").click().run()
    no_exception(at, "Upload : la confirmation s'execute sans exception")
    txt = page_text(at)
    check("Upload : confirmation appelee avec file_id et categorie",
          ("a1b2c3d4", "Guides pratiques") in fake.args("confirm_args"), str(fake.args("confirm_args")))
    check("Upload : etape 4 affiche la classification confirmee", "classification confirmee" in txt)
    check("Upload : nombre de chunks indexes affiche", "chunks indexes" in txt and "12" in txt)


def test_upload_cas_confiance_moyenne() -> None:
    fake = scenario()
    fake.upload_resp = upload_resp(
        0.72, "Procédures",
        alternatives=[{"categorie": "Guides pratiques", "probabilite": 0.2},
                      {"categorie": "Règlements", "probabilite": 0.08}],
    )
    fake.confirm_resp = {"status": "success", "message": "ok", "source_file": "x.txt",
                         "categorie": "Guides pratiques", "indexe": True, "nb_chunks": 5}
    at = run(PAGE_UPLOAD)
    _depot(at, "Texte de test suffisamment long pour etre classe par le modele local.")
    button(at, "Continuer vers la proposition").click().run()
    no_exception(at, "Upload : confiance moyenne s'affiche sans exception")
    txt = page_text(at)
    check("Upload : confiance 60-80 % -> 'Plusieurs categories possibles'",
          "plusieurs categories possibles" in txt)
    check("Upload : alternatives avec probabilites affichees",
          "guides pratiques" in txt and "20 %" in txt and "72 %" in txt)
    check("Upload : liste de choix proposee (5 categories)",
          len(at.selectbox) >= 1 and len(at.selectbox[0].options) == 5)
    set_option(at, 0, "Guides pratiques")
    button(at, "Valider ce choix").click().run()
    check("Upload : validation avec la categorie choisie",
          ("a1b2c3d4", "Guides pratiques") in fake.args("confirm_args"), str(fake.args("confirm_args")))


def test_upload_cas_confiance_faible() -> None:
    fake = scenario()
    fake.upload_resp = upload_resp(0.41, "Règlements")
    fake.confirm_resp = {"status": "success", "message": "ok", "source_file": "x.txt",
                         "categorie": "Formulaires & documents ponctuels", "indexe": True, "nb_chunks": 3}
    at = run(PAGE_UPLOAD)
    _depot(at, "Texte de test suffisamment long pour etre classe par le modele local.")
    button(at, "Continuer vers la proposition").click().run()
    no_exception(at, "Upload : confiance faible s'affiche sans exception")
    txt = page_text(at)
    check("Upload : confiance < 60 % -> 'Confiance trop faible'", "confiance trop faible" in txt)
    check("Upload : aucune categorie preselectionnee (placeholder)",
          len(at.selectbox) >= 1 and "choisissez" in norm(at.selectbox[0].value),
          str([s.value for s in at.selectbox]))
    bouton = button(at, "Confirmer ma sélection")
    check("Upload : confirmation desactivee tant que rien n'est choisi",
          bouton is not None and bouton.disabled, str(bouton and bouton.disabled))
    set_option(at, 0, "Formulaires")
    bouton = button(at, "Confirmer ma sélection")
    check("Upload : confirmation activee apres choix manuel", bouton is not None and not bouton.disabled)
    bouton.click().run()
    check("Upload : confirmation avec la categorie choisie a la main",
          any(a[0] == "a1b2c3d4" and a[1].startswith("Formulaires") for a in fake.args("confirm_args")),
          str(fake.args("confirm_args")))


def test_upload_erreurs_et_exemple() -> None:
    fake = scenario(down=True)
    at = run(PAGE_UPLOAD)
    if not no_exception(at, "Upload : page s'execute sans exception (API arretee)"):
        return
    check("Upload : message 'API hors ligne' visible au demarrage",
          "connexion impossible" in page_text(at))
    button(at, "Charger un exemple").click().run()
    check("Upload : 'Charger un exemple' remplit le texte d'exemple",
          "guide des bourses" in norm(at.text_area[0].value))
    _depot(at, "Un texte suffisant pour declencher un appel vers l'API arretee.")
    no_exception(at, "Upload : analyse avec API arretee sans exception")
    check("Upload : erreur de connexion affichee, pas de crash",
          "connexion impossible" in page_text(at) and "lancez" in page_text(at))

    scenario()
    at = run(PAGE_UPLOAD)
    _depot(at, "")
    check("Upload : avertissement si aucun contenu",
          any("deposez un fichier" in norm(w.value) for w in at.warning))

    fake = scenario()
    fake.upload_resp = upload_resp(0.93)
    fake.confirm_error = "Fichier temporaire introuvable ou expire."
    at = run(PAGE_UPLOAD)
    _depot(at, "Texte de test suffisamment long pour etre classe par le modele local.")
    button(at, "Continuer vers la proposition").click().run()
    button(at, "Confirmer la catégorie").click().run()
    no_exception(at, "Upload : erreur 404 a la confirmation sans exception")
    check("Upload : message d'erreur de confirmation affiche",
          "fichier temporaire introuvable" in page_text(at))

    fake = scenario()
    fake.upload_resp = upload_resp(0.93)
    fake.confirm_resp = {"status": "success", "message": "ok", "source_file": "x.txt",
                         "categorie": "Guides pratiques", "indexe": False, "nb_chunks": 0}
    at = run(PAGE_UPLOAD)
    _depot(at, "Texte de test suffisamment long pour etre classe par le modele local.")
    button(at, "Continuer vers la proposition").click().run()
    button(at, "Confirmer la catégorie").click().run()
    check("Upload : document confirme mais non indexe signale",
          "pas indexe" in page_text(at))


# --- 8. Questions & Reponses ----------------------------------------------
def test_questions() -> None:
    fake = scenario()
    fake.query_resp = {
        "question": "x", "reponse": "Une moyenne generale superieure a 12/20 est exigee.",
        "sources": [{"fichier": "02_guide_bourses.txt", "categorie": "Guides pratiques",
                     "extrait": "Pour le renouvellement : maintenir une moyenne d'au moins 12/20."}],
        "filtre": "aucun (tous les documents)", "temps_ms": 1234.5, "nb_chunks_trouves": 4,
    }
    at = run(PAGE_QUESTIONS)
    if not no_exception(at, "Questions : la page s'execute sans exception"):
        return
    check("Questions : filtres de perimetre presents",
          "perimetre" in page_text(at) and "tous les documents" in page_text(at))
    check("Questions : reglage du nombre de sources (1 a 20)",
          any(norm(s.label) == "sources affichees" and s.min == 1 and s.max == 20 for s in at.slider))
    check("Questions : composer de saisie present", len(at.chat_input) == 1)

    at.chat_input[0].set_value("Quelles sont les conditions pour obtenir une bourse ?").run()
    no_exception(at, "Questions : question envoyee sans exception")
    txt = page_text(at)
    check("Questions : la question apparait dans la conversation",
          "conditions pour obtenir une bourse" in txt)
    check("Questions : la reponse de l'API est affichee", "moyenne generale superieure a 12/20" in txt)
    check("Questions : les sources sont citees",
          any("sources" in norm(e.label) for e in at.expander) and "02_guide_bourses.txt" in txt)
    check("Questions : latence et extraits affiches", "latence" in txt and "1.2 s" in txt
          and "extraits trouves" in txt)
    check("Questions : n_results transmis (4 par defaut)",
          any(a[1] == 4 and a[2] is None and a[3] is None for a in fake.args("query_args")),
          str(fake.args("query_args")))

    at2 = run(PAGE_QUESTIONS)
    set_option(at2, 0, "Par catégorie")
    no_exception(at2, "Questions : changement de perimetre sans exception")
    at2.chat_input[0].set_value("Comment se deroule l'inscription ?").run()
    check("Questions : filtre categorie transmis a l'API",
          any(a[2] == "Règlements" for a in fake.args("query_args")),
          str(fake.args("query_args")[-1:]))

    btn = button(at2, "Reinitialiser")
    check("Questions : bouton Reinitialiser present", btn is not None)
    if btn is not None:
        avant = len(at2.chat_message)
        btn.click().run()
        check("Questions : conversation reinitialisee",
              len(at2.chat_message) == 1 and avant > 1, f"{avant} avant, {len(at2.chat_message)} apres")

    at3 = run(PAGE_QUESTIONS)
    set_option(at3, 0, "Par fichier")
    no_exception(at3, "Questions : perimetre par fichier sans exception")
    check("Questions : liste de fichiers confirmes proposee",
          len(at3.selectbox) >= 2 and "02_guide_bourses.txt" in at3.selectbox[1].options)


def test_questions_erreurs() -> None:
    fake = scenario()
    fake.query_resp = {"reponse": "[MOCK] 1 extrait(s) trouve(s). RAG reel indisponible.",
                       "sources": [], "filtre": "aucun (tous les documents)",
                       "temps_ms": 10.0, "nb_chunks_trouves": 0}
    at = run(PAGE_QUESTIONS)
    at.chat_input[0].set_value("Question en mode degrade ?").run()
    no_exception(at, "Questions : reponse en mode degrade sans exception")
    check("Questions : mode degrade signale a l'utilisateur", "mode degrade" in page_text(at))

    scenario(down=True)
    at = run(PAGE_QUESTIONS)
    at.chat_input[0].set_value("Question avec API arretee ?").run()
    no_exception(at, "Questions : API arretee sans exception")
    check("Questions : panne affichee dans la conversation", "lancez le backend" in page_text(at))
    check("Questions : la page reste utilisable (composer present)", len(at.chat_input) == 1)


# --- 9. Tableau de bord ----------------------------------------------------
def test_dashboard() -> None:
    scenario()
    at = run(PAGE_DASHBOARD)
    if not no_exception(at, "Dashboard : la page s'execute sans exception"):
        return
    txt = page_text(at)
    check("Dashboard : 4 indicateurs cles", all(k in txt for k in
          ["documents", "chunks indexes", "non indexes", "modele"]))
    check("Dashboard : categories couvertes calculees depuis l'API (3 / 5)",
          "3 / 5 categories couvertes" in txt, txt[:200])
    check("Dashboard : chunks indexes lus depuis /api/health (200)", "200" in txt)
    check("Dashboard : repartition par categorie", "repartition par categorie" in txt)
    check("Dashboard : graphique des chunks par categorie", len(at.get("vega_lite_chart")) >= 1,
          str(len(at.get("vega_lite_chart"))) + " graphique(s)")
    check("Dashboard : tableau des documents recents", len(at.dataframe) >= 1)
    check("Dashboard : documents non indexes signales", "a indexer" in txt)
    check("Dashboard : bloc qualite systeme", "qualite du systeme" in txt)
    check("Dashboard : export CSV disponible", len(at.get("download_button")) == 1)
    check("Dashboard : aucune statistique simulee (questions / activite absentes)",
          "questions posees" not in txt and "activite des 7 derniers jours" not in txt)

    scenario(down=True)
    at = run(PAGE_DASHBOARD)
    if no_exception(at, "Dashboard : API arretee sans exception"):
        check("Dashboard : erreur de connexion affichee", "connexion impossible" in page_text(at))
        check("Dashboard : pas d'export quand l'API est arretee", len(at.get("download_button")) == 0)


# --- 10. Controles transverses --------------------------------------------
def test_transverse() -> None:
    css = (INTERFACE / "assets" / "style.css").read_text(encoding="utf-8", errors="replace")
    check("Design : CSS du design system present", len(css) > 3000, str(len(css)) + " caracteres")
    check("Design : aucune ressource externe dans le CSS", "http://" not in css and "https://" not in css)

    fichiers = list(INTERFACE.glob("*.py")) + list((INTERFACE / "pages").glob("*.py"))
    reseau = [f.name for f in fichiers
              if re.search(r"^\s*(import httpx|import openai|from openai|import urllib)",
                           f.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)]
    check("Offline : aucune bibliotheque reseau hors api_client.py", not reseau, str(reseau))
    # Autorisees : adresse locale de l'API et namespace SVG (pas une requete reseau).
    urls = []
    for f in fichiers:
        for url in re.findall(r"https?://[^\s\"')]+", f.read_text(encoding="utf-8", errors="replace")):
            if not re.match(r"https?://(127\.0\.0\.1|localhost)(:\d+)?", url) and "w3.org" not in url:
                urls.append(f.name + " : " + url)
    check("Offline : aucune URL externe dans l'interface", not urls, str(urls))
    appels = [f.name for f in fichiers
              if re.search(r"^\s*(import requests|from requests)", f.read_text(encoding="utf-8", errors="replace"),
                           re.MULTILINE)]
    check("Architecture : seul api_client.py appelle requests", appels in ([], ["api_client.py"]), str(appels))
    check("Structure : point d'entree interface/app.py present", Path(APP).exists())


# --- 11. Main --------------------------------------------------------------
def main() -> int:
    say("")
    say("=" * 62)
    say("  Tests interface DocuClassif AI - partie B1 (Jour 6)")
    say("=" * 62)
    say("")

    for fn in (test_structure, test_api_client_unit, test_accueil,
               test_upload_cas_confiance_haute, test_upload_cas_confiance_moyenne,
               test_upload_cas_confiance_faible, test_upload_erreurs_et_exemple,
               test_questions, test_questions_erreurs, test_dashboard, test_transverse):
        try:
            fn()
        except Exception:
            detail = traceback.format_exc(limit=3)
            results.append((False, fn.__name__ + " : exception inattendue", detail))
            say("[ECHEC] " + fn.__name__ + " : exception inattendue")
            say(detail)
        say("")

    ok = sum(1 for r in results if r[0])
    ko = len(results) - ok
    say("=" * 62)
    if ko:
        say("  RESULTAT : " + str(ok) + "/" + str(len(results)) + " tests reussis - " + str(ko) + " ECHEC(S)")
    else:
        say("  RESULTAT : " + str(ok) + "/" + str(len(results)) + " tests reussis - TOUT EST VERT")
    say("=" * 62)

    if ko:
        say("")
        say("Echecs a corriger :")
        for passed, name, detail in results:
            if not passed:
                say("  - " + name)
                for ligne in str(detail).splitlines():
                    say("      " + ligne)
    say("")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
