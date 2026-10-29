"""
test_ui_b1.py - Tests automatiques de la maquette (Jour 3, partie B1).

Aucun navigateur necessaire : on utilise streamlit.testing.v1.AppTest,
qui execute reellement les pages Streamlit et simule les clics / saisies.

Lancement (depuis la racine du projet) :

    python tests/test_ui_b1.py

Sortie : une ligne [OK] / [ECHEC] par test, un resume, et un code de sortie
non nul si un test echoue.

Fichier volontairement 100% ASCII (ni accents, ni emoji) : la console Windows
est souvent en cp1252 et levee d'erreur "UnicodeEncodeError: 'charmap'" sur
les caracteres non latins. Les comparaisons avec le texte de l'interface sont
faites sans accents (fonction norm), donc les accents de l'UI ne genent pas.

Dependance : streamlit >= 1.28 (AppTest). Rien d'autre.
"""

from __future__ import annotations

import logging
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


# --- 2. Imports Streamlit --------------------------------------------------
INTERFACE = Path(__file__).resolve().parent.parent / "interface"
sys.path.insert(0, str(INTERFACE))

from streamlit.testing.v1 import AppTest  # noqa: E402

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
results = []


# --- 3. Outils -------------------------------------------------------------
def run(path: str) -> AppTest:
    at = AppTest.from_file(path, default_timeout=TIMEOUT)
    at.run()
    return at


def page_text(at: AppTest) -> str:
    """Texte visible d'une page, sans accents (voir norm)."""
    chunks = []
    for groupe in ("html", "markdown", "caption", "title", "header", "subheader"):
        chunks += [str(el.value) for el in at.get(groupe)]
    chunks += [str(b.label) for b in at.button]
    chunks += [str(c.label) for c in at.selectbox]
    chunks += [str(e.label) for e in at.expander]
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
    "Could not find page": "interface/app.py est l'ANCIENNE version (pages/Upload.py). "
                           "Voir GUIDE_INSTALLATION_B1.md etape 2.",
    "No module named 'nav'": "lance python -m streamlit run interface/app.py, et verifie que "
                             "nav.py / theme.py / data_mock.py sont dans interface/.",
    "No module named 'streamlit'": "active le venv et installe interface/requirements.txt.",
    "Multiple Pages specified": "il reste un doublon dans interface/pages/ : supprime tout "
                                "fichier autre que 1_Upload.py / 2_Questions.py / 3_Dashboard.py.",
    "No module named 'data_mock'": "data_mock.py manque dans interface/ : re-extrais l'archive.",
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


# --- 4. Structure du projet (detecte les restes de l'ancienne version) -----
def test_structure() -> None:
    pages_dir = INTERFACE / "pages"

    check("Structure : les 3 pages du plan existent",
          all((pages_dir / nom).exists() for nom in PAGES_ATTENDUES),
          str(sorted(p.name for p in pages_dir.glob("*.py"))))

    restes = [p.name for p in pages_dir.glob("*.py") if p.name not in PAGES_ATTENDUES]
    check("Structure : aucun fichier de page en trop (restes de l'ancienne version)",
          not restes, "a supprimer dans interface/pages/ : " + str(restes))

    app_src = Path(APP).read_text(encoding="utf-8", errors="replace")
    check("Structure : app.py est la nouvelle version (pas de st.page_link)",
          "st.page_link(" not in app_src,
          "interface/app.py est l'ancienne version : GUIDE_INSTALLATION_B1.md etape 2")

    import nav  # import tardif volontaire

    manquantes = [cible for _, _, _, cible in nav.NAV if not (INTERFACE / cible).exists()]
    check("Structure : toutes les cibles de navigation existent",
          not manquantes, "cibles introuvables : " + str(manquantes))

    for fichier in sorted(pages_dir.glob("*.py")):
        at = AppTest.from_file(str(fichier), default_timeout=TIMEOUT)
        at.run()
        no_exception(at, "Structure : la page " + fichier.name + " s'execute sans exception")


# --- 5. Accueil -----------------------------------------------------------
def test_accueil() -> None:
    at = run(APP)
    if not no_exception(at, "Accueil : la page s'execute sans exception"):
        return
    txt = page_text(at)

    check("Accueil : titre et accroche presents",
          "docuclassif ai" in txt and "classification intelligente" in txt)
    check("Accueil : les 4 modules sont affiches",
          all(m in txt for m in ["classification automatique", "questions & reponses sourcees",
                                 "souverainete des donnees", "tableau de bord"]))
    check("Accueil : les 5 categories sont affichees",
          all(c in txt for c in ["reglements", "guides pratiques", "procedures",
                                 "organisation", "formulaires"]))
    check("Accueil : badge 100 % offline visible", "100 % offline" in txt)
    check("Accueil : parcours en 3 etapes", "demarrage rapide" in txt)

    labels = [b.label for b in at.button]
    check("Sidebar : 4 entrees de navigation",
          all(l in labels for l in ["Accueil", "Upload", "Questions", "Tableau de bord"]),
          str(labels))
    check("Accueil : actions principales presentes",
          "Uploader un document" in labels and "Poser une question" in labels)


# --- 6. Upload & Classification -------------------------------------------
def test_upload() -> None:
    at = run(PAGE_UPLOAD)
    if not no_exception(at, "Upload : la page s'execute sans exception"):
        return
    txt = page_text(at)

    check("Upload : zone de depot de fichier presente", len(at.get("file_uploader")) == 1)
    check("Upload : etat vide affiche avant analyse", "aucun document analyse" in txt)

    btn = button(at, "Charger un exemple")
    check("Upload : bouton 'Charger un exemple' present", btn is not None)
    if btn is None:
        return
    btn.click().run()
    if not no_exception(at, "Upload : l'analyse simulee s'execute sans exception"):
        return
    txt = page_text(at)

    check("Upload : une categorie est proposee", "guides pratiques" in txt)
    check("Upload : la jauge de confiance affiche un pourcentage",
          "%" in txt and "confiance" in txt)
    check("Upload : les autres hypotheses sont affichees",
          "autres hypotheses" in txt or "confiance faible" in txt)
    check("Upload : les 5 categories proposees a la correction",
          len(at.selectbox) >= 1 and len(at.selectbox[0].options) == 5,
          str(at.selectbox[0].options if at.selectbox else []))
    check("Upload : boutons Confirmer / Rejeter presents",
          button(at, "Confirmer la categorie") is not None and button(at, "Rejeter") is not None)

    button(at, "Confirmer la categorie").click().run()
    no_exception(at, "Upload : la confirmation s'execute sans exception")
    txt = page_text(at)
    check("Upload : etat confirme affiche", "classification confirmee" in txt)
    check("Upload : actions post-confirmation", button(at, "Analyser un autre document") is not None)

    button(at, "Analyser un autre document").click().run()
    check("Upload : reinitialisation vers l'etat vide", "aucun document analyse" in page_text(at))

    at2 = run(PAGE_UPLOAD)
    button(at2, "Analyser le document").click().run()
    no_exception(at2, "Upload : analyse a vide geree sans exception")
    check("Upload : avertissement si aucun contenu",
          any("deposez un fichier" in norm(w.value) for w in at2.warning))
    check("Upload : tableau des classifications recentes", len(at2.dataframe) == 1)


# --- 7. Questions & Reponses ----------------------------------------------
def test_questions() -> None:
    at = run(PAGE_QUESTIONS)
    if not no_exception(at, "Questions : la page s'execute sans exception"):
        return
    txt = page_text(at)

    check("Questions : filtres de perimetre presents",
          "perimetre" in txt and "tous les documents" in txt)
    check("Questions : reglage du nombre de sources",
          any(norm(s.label) == "sources affichees" for s in at.slider),
          str([s.label for s in at.slider]))
    check("Questions : suggestions de questions", "exemples de questions" in txt)
    check("Questions : composer de saisie present", len(at.chat_input) == 1)

    at.chat_input[0].set_value("Quelles sont les conditions pour obtenir une bourse ?").run()
    if not no_exception(at, "Questions : generation de la reponse sans exception"):
        return
    txt = page_text(at)

    check("Questions : la question apparait dans la conversation",
          "conditions pour obtenir une bourse" in txt)
    check("Questions : la reponse est generee", "moyenne generale superieure a 12/20" in txt)
    check("Questions : les sources sont citees",
          any("sources" in norm(e.label) for e in at.expander)
          and "02_guide_bourses.docx" in txt,
          str([e.label for e in at.expander]))
    check("Questions : metriques de reponse (latence / pertinence)",
          "latence" in txt and "pertinence" in txt)

    at2 = run(PAGE_QUESTIONS)
    set_option(at2, 0, "Par categorie")
    no_exception(at2, "Questions : changement de perimetre sans exception")
    check("Questions : filtre categorie applique", "recherche limitee a" in page_text(at2))
    at2.chat_input[0].set_value("Comment se deroule l'inscription ?").run()
    check("Questions : reponse avec filtre categorie",
          "inscription" in page_text(at2))

    btn = button(at2, "Reinitialiser")
    check("Questions : bouton Reinitialiser present", btn is not None)
    if btn is not None:
        avant = len(at2.chat_message)
        btn.click().run()
        check("Questions : conversation reinitialisee",
              len(at2.chat_message) == 1 and avant > 1,
              str(avant) + " message(s) avant, " + str(len(at2.chat_message)) + " apres")

    at3 = run(PAGE_QUESTIONS)
    set_option(at3, 0, "Par fichier")
    no_exception(at3, "Questions : perimetre par fichier sans exception")
    check("Questions : liste de fichiers proposee",
          len(at3.selectbox) >= 2 and "01_reglement_interieur.pdf" in at3.selectbox[1].options)


# --- 8. Tableau de bord ---------------------------------------------------
def test_dashboard() -> None:
    at = run(PAGE_DASHBOARD)
    if not no_exception(at, "Dashboard : la page s'execute sans exception"):
        return
    txt = page_text(at)

    check("Dashboard : 4 indicateurs cles",
          all(k in txt for k in ["documents", "chunks", "questions posees", "classifications"]))
    check("Dashboard : repartition par categorie", "repartition par categorie" in txt)
    check("Dashboard : graphiques Altair presents (barres + courbe)",
          len(at.get("vega_lite_chart")) >= 2,
          str(len(at.get("vega_lite_chart"))) + " graphique(s)")
    check("Dashboard : courbe d'activite presente", "activite des 7 derniers jours" in txt)
    check("Dashboard : tableau des documents recents",
          len(at.dataframe) >= 1 and len(at.dataframe[0].value) > 0)
    check("Dashboard : bloc qualite systeme", "qualite du systeme" in txt)
    check("Dashboard : export CSV disponible", len(at.get("download_button")) == 1)


# --- 9. Controles transverses --------------------------------------------
def test_transverse() -> None:
    css = (INTERFACE / "assets" / "style.css").read_text(encoding="utf-8", errors="replace")
    check("Design : CSS du design system present", len(css) > 3000, str(len(css)) + " caracteres")
    check("Design : aucune ressource externe dans le CSS", "http://" not in css and "https://" not in css)

    import re

    sources = list(INTERFACE.glob("*.py")) + list((INTERFACE / "pages").glob("*.py"))
    reseau = [f.name for f in sources
              if re.search(r"^\s*(import requests|from requests|import httpx|import openai)",
                           f.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)]
    check("Offline : aucune dependance reseau dans l'interface", not reseau, str(reseau))
    check("Structure : point d'entree interface/app.py present", Path(APP).exists())


# --- 10. Main -------------------------------------------------------------
def main() -> int:
    say("")
    say("=" * 62)
    say("  Tests interface DocuClassif AI - partie B1 (Jour 3)")
    say("=" * 62)
    say("")

    for fn in (test_structure, test_accueil, test_upload, test_questions,
               test_dashboard, test_transverse):
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
        say("  RESULTAT : " + str(ok) + "/" + str(len(results)) + " tests reussis - "
            + str(ko) + " ECHEC(S)")
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