# -*- coding: utf-8 -*-
"""
Nettoyage des textes extraits (Jour 2, Partie 3).

Version mise à jour, adaptée au corpus réel de doc_rag/processed
(16 fichiers UVK inspectés un par un), sans avoir à adapter le code
fichier par fichier :

- BRUIT RÉEL DU CORPUS, traité explicitement : en-tête courant
  « UNIVERSITÉ DE LA VAKINANKARATRA (UVK)  |  <titre du document> »
  (40 occurrences, dont une seule dans les documents de 2 pages :
  impossible à repérer par simple fréquence) et pied de page
  « Année académique 2026 – 2027  —  Page X » (52 occurrences).
  Les deux sont supprimés partout : l'institution et le titre figurent
  déjà en page de garde, aucune information n'est perdue.
- EN-TÊTES / PIEDS DE PAGE dÉTECTÉS AUTOMATIQUEMENT en plus : au lieu de coder en
  dur des motifs comme « Règlement intérieur » (qui ne marchent que pour un
  seul document), le script repère toutes les lignes courtes qui se
  répètent d'une page à l'autre (en ignorant les numéros qui changent) et
  les supprime, en gardant la 1re occurrence pour ne perdre aucune info.
- Numéros de page sous toutes leurs formes : "12", "- 12 -", "Page 12",
  "Page 12 sur 45", "12/45"...
- Réparation de l'encodage cassé (Ã© -> é) et des caractères typographiques
  (’ « » — …) que l'ancien script SUPPRIMAIT (l’université devenait
  "luniversité" !).
- Ligatures PDF (ﬁ -> fi), césures de fin de ligne (informa-tion scindé
  recollé), mots coupés, sauts de ligne au milieu des phrases recollés en
  paragraphes, sommaires avec points de suite (..... 12), © / URL isolés
  en pied de page.
- Artefacts vus dans CE corpus : tableaux aplatis dont les colonnes ont
  disparu (lignes courtes à montants/dates, préservées ligne par ligne
  au lieu d'être fondues dans un paragraphe), mots collés à la jonction
  des colonnes (« 2027Enseignements », « précédent1 semestre »,
  « bourses@uvk.mgLun » -> espace réinsérée), « l' unité » -> « l'unité »,
  cases à cocher ☐ transformées en puces de liste, gras Markdown
  résiduel **...**, séparateurs en tirets cadratins (fichiers 17-20),
  et phrases/tableaux coupés par un changement de page recollés.
  Les deux familles d'extraction du corpus sont gérées : lignes
  visuelles courtes type PDF (01-12) et paragraphes longs séparés par
  des lignes vides type Word (17-20).
  Les symboles utiles sont CONSERVÉS : ≥, ≤, °, §, œ, %, <, >
  (critères du type « moyenne ≥ 14/20 », « revenu < 300 000 Ar »).
- Les titres de structure ("Article 12", "Chapitre 3", titres en
  MAJUSCULES), les listes et les tableaux sont PRÉSERVÉS : ils ne sont
  jamais pris pour des en-têtes répétés.

Utilisation (depuis la racine du projet) :
    python src/ingestion/clean.py

Le dossier d'entrée est cherché automatiquement, dans cet ordre :
doc_rag/processed/ -> doc_rag/raw/ -> data/processed/ -> data/raw/ -> raw/...
Pour forcer un dossier :
    python src/ingestion/clean.py doc_rag/processed
    python src/ingestion/clean.py --output data/processed

Comportement par défaut (pensé pour que chunk.py marche ensuite sans
modification) :
- Entrée = .../processed (doc_rag/processed ou data/processed)
  -> nettoyage sur place, MAIS les originaux sont d'abord copiés dans
  processed/_backup_avant_nettoyage/ (backup jamais écrasé : on peut
  relancer clean.py sans risque).
- Entrée = doc_rag/raw -> sortie dans doc_rag/processed/ ;
  Entrée = data/raw    -> sortie dans data/processed/.
  Dans les deux cas, les fichiers de raw/ ne sont PAS touchés.

Aucune bibliothèque à installer : uniquement la bibliothèque standard.
"""

import argparse
import json
import re
import shutil
import sys
import unicodedata
from collections import Counter
from pathlib import Path

# Console Windows : éviter le crash sur les accents / emoji (cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Réglages (modifiables)
# ---------------------------------------------------------------------------
EXTENSIONS = {".txt", ".md"}
MIN_REPETITIONS_ENTETE = 3        # répétitions min. pour suspecter un en-tête
RATIO_PAGES_ENTETE = 0.35         # ... ou présent sur >= 35 % des pages estimées
CHARS_PER_PAGE_ESTIMATE = 1800    # estimation nb de pages si pas de marqueur
BACKUP_DIR_NAME = "_backup_avant_nettoyage"
REPORT_NAME = "_clean_report.json"

CANDIDATE_INPUT_DIRS = [
    "doc_rag/processed",
    "doc_rag/raw",
    "data/processed",
    "data/raw",
    "raw",
    "processed",
]

# Titres de structure : JAMAIS supprimés, même s'ils se répètent.
PROTECTED_HEADING_RE = re.compile(
    r"^(article|art\.|chapitre|section|titre|partie|livre|annexe|"
    r"paragraphe|§|alinéa)\b",
    re.IGNORECASE,
)
# Titre numéroté : "2.3 La bourse...", "10. Contacts". Une année en
# début de ligne ("2027 Enseignements...") n'est PAS une numérotation.
NUMBERED_HEADING_RE = re.compile(
    r"^(?:\d{1,2}(?:\.\d{1,2})*[.)]?|\d{1,3}[.)])\s+[A-ZÀ-ÖØ-Þ]")
LIST_ITEM_RE = re.compile(r"^([\-*+•·☐☑☒✓✔]|\d{1,3}[.)]|[a-zA-Z][.)])\s+\S")
PAGE_MARKER = "\x0c"  # saut de page (\f) produit par PyPDF2 / pdfplumber

# Pied de page réel du corpus doc_rag/processed (52 occurrences), après
# normalisation des tirets en "-" et compression des espaces :
#   "Année académique 2026 - 2027 - Page 6"
ACADEMIC_YEAR_FOOTER_RE = re.compile(
    r"^année académique\s+\d{4}\s*[-/]\s*\d{4}\s*[-|]\s*page\s*\d+$")

# Formules de clôture / signatures : jamais des lignes de tableau.
CLOSING_LINE_RE = re.compile(
    r"^(fait à\b|fait en\b|lu et approuvé|le recteur,|le président.*,$|"
    r"le doyen.*,$|le secrétaire.*,$|le directeur.*,$|signatures?\b.*:?$)",
    re.IGNORECASE)

# Ligne de tableau se terminant par une abréviation de mois ("15 jan.") :
# ce n'est pas une fin de phrase.
MONTH_ABBR_END_RE = re.compile(
    r"\b(jan|janv|févr|fevr|avr|juil|sept|oct|nov|déc|dec)\.$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# 1. Réparation d'encodage et normalisation des caractères
# ---------------------------------------------------------------------------
_MOJIBAKE_MARKERS = ("Ã©", "Ã¨", "Ãª", "Ã ", "Ã´", "Ã®", "Ã§", "Ã‰", "Â«", "Â»", "Ã»", "Ã¯")


def _mojibake_score(text):
    return sum(text.count(m) for m in _MOJIBAKE_MARKERS) + text.count("�")


def repair_mojibake(text):
    """Répare le double encodage UTF-8 lu en latin-1 (Ã© -> é)."""
    if _mojibake_score(text) < 3:
        return text, False
    for enc in ("cp1252", "latin-1"):
        try:
            fixed = text.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if _mojibake_score(fixed) < _mojibake_score(text):
            return fixed, True
    return text, False


_CHAR_REPLACEMENTS = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "`": "'", "´": "'",
    "“": '"', "”": '"', "«": '"', "»": '"', "‹": "'", "›": "'",
    "–": "-", "—": "-", "‐": "-", "‑": "-", "−": "-",
    "…": "...",
    "\u00a0": " ", "\u202f": " ", "\u2007": " ",
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
    "\u00ad": "",            # tiret mou (césure invisible dans les PDF)
    "�": "",            # caractère de remplacement (extraction ratée)
    "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": "",
}
# Puces PDF dans les polices privées / symboles -> puce lisible
_BULLET_CHARS = dict.fromkeys("•▪▫■□◆◇◦\u2023\u2043\uf0b7\uf0a7", "-")


def normalize_characters(text):
    # Gras Markdown résiduel dans certaines extractions Word : **texte**
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    for bad, good in _CHAR_REPLACEMENTS.items():
        if bad in text:
            text = text.replace(bad, good)
    for bad, good in _BULLET_CHARS.items():
        if bad in text:
            text = text.replace(bad, good)
    text = unicodedata.normalize("NFC", text)
    # Supprimer les caractères de contrôle et la zone privée (glyphes PDF),
    # SAUF saut de ligne, tabulation et saut de page (utilisé plus bas).
    out = []
    for ch in text:
        if ch in ("\n", "\t", PAGE_MARKER):
            out.append(ch)
        elif unicodedata.category(ch)[0] == "C":  # Cc, Cf, Co, Cs, Cn
            continue
        else:
            out.append(ch)
    return "".join(out)


def repair_glued_words(line):
    """Mots collés quand l'extraction perd la frontière de colonne :
    '2027Enseignements', 'précédent1 semestre', 'bourses@uvk.mgLun',
    '(M2)Convention', et « l' unité » -> « l'unité ». Règles prudentes :
    jamais dans un sigle (M2, L3) ni dans un horaire (7h30)."""
    # l' unité -> l'unité (apostrophe d'élision suivie d'une espace)
    line = re.sub(r"\b([lLdDnNsSjJ])'\s+(?=[A-Za-zÀ-ÖØ-öø-ÿ])", r"\1'", line)
    # minuscules puis Majuscule = nouveau mot : semestreConnaissances
    line = re.sub(r"(?<=[a-zà-öø-ÿ]{2})(?=[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]{2,})", " ", line)
    # chiffre puis Majuscule = nouveau mot : 2027Vacances
    line = re.sub(r"(?<=\d)(?=[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]{2,})", " ", line)
    # mot (>= 3 lettres) puis nombre entier : précédent1, thèse1
    # (le \b initial protège 7h30, 16h30 : le 'h' n'est pas en début de mot)
    line = re.sub(r"\b([A-Za-zÀ-ÖØ-öø-ÿ]{3,})(?=\d)", r"\1 ", line)
    # parenthèse fermante collée au mot suivant : (M2)Convention
    line = re.sub(r"(?<=[)\]])(?=[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]{2,})", " ", line)
    return line


# ---------------------------------------------------------------------------
# 2. Aide : classification des lignes
# ---------------------------------------------------------------------------
def is_protected_heading(line):
    return bool(PROTECTED_HEADING_RE.match(line) or NUMBERED_HEADING_RE.match(line))


def is_list_item(line):
    return bool(LIST_ITEM_RE.match(line))


def is_table_line(line):
    return " | " in line


def uppercase_ratio(line):
    letters = [c for c in line if c.isalpha()]
    if len(letters) < 3:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def is_heading_line(line):
    if is_table_line(line):          # un en-tête de tableau n'est pas un titre
        return False
    if line.startswith("#"):
        return True
    if is_protected_heading(line):
        return True
    # Ligne d'intro se terminant par ":"... mais pas si c'est la suite
    # d'une phrase ("d'insertion. Les modalités varient selon le cycle :")
    if (len(line) <= 90 and line.endswith(":") and not line[0].islower()
            and ". " not in line[:-1]):
        return True
    if len(line) <= 90 and not line.endswith((".", ",", ";", "!", "?")):
        if uppercase_ratio(line) >= 0.7:
            return True
    return False


def repeated_key(line):
    """Clé de comparaison : minuscules, chiffres -> #, espaces compressés.
    "Université - Page 12" et "Université - Page 13" donnent la même clé."""
    key = re.sub(r"\d+", "#", line.lower())
    key = re.sub(r"\s+", " ", key).strip(" -.|/")
    return key


def capitalized_word_ratio(line):
    """Part des mots (hors 1er) contenant une majuscule. Élevée pour un
    en-tête ("Ministère de l'Enseignement Supérieur"), faible pour une
    ligne de corps de texte ("Les étudiants doivent respecter le...")."""
    words = re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)*", line, flags=re.UNICODE)
    rest = [w for w in words[1:] if len(w) >= 2]
    if not rest:
        return 0.0
    return sum(1 for w in rest if any(c.isupper() for c in w)) / len(rest)


def looks_like_header(line):
    return uppercase_ratio(line) >= 0.6 or capitalized_word_ratio(line) >= 0.5


def base_candidate_ok(line):
    """Filtres communs : une ligne trop longue, structurée ou 'phrase'
    ne peut pas être un en-tête répété."""
    if not line or len(line) > 110 or len(line.split()) > 14:
        return False
    if sum(1 for c in line if c.isalpha()) < 3:
        return False
    if is_protected_heading(line) or is_list_item(line):
        return False
    if line.endswith((":", "-")):                    # intro ou mot coupé
        return False
    if line.endswith(".") and len(line) > 40:        # vraie phrase
        return False
    return True


def detect_page_headers(text):
    """Si l'extraction conserve les sauts de page (\\f), seuls les débuts
    et fins de page peuvent être des en-têtes/pieds : méthode fiable."""
    if PAGE_MARKER not in text:
        return set(), 0
    page_lines = []
    for chunk in text.split(PAGE_MARKER):
        stripped = [ln.strip() for ln in chunk.split("\n") if ln.strip()]
        if stripped:
            page_lines.append(stripped)
    n_pages = len(page_lines)
    if n_pages < 3:
        return set(), n_pages
    counts = Counter()
    for page in page_lines:
        border = page[:2] + page[-2:]
        keys = {repeated_key(ln) for ln in border
                if base_candidate_ok(re.sub(r" {2,}", " ", ln))}
        counts.update(k for k in keys if k)
    threshold = max(2, int(0.5 * n_pages + 0.5))
    return {k for k, n in counts.items() if n >= threshold}, n_pages


def detect_table_lines(lines, heading_idx):
    """Tableaux dont les colonnes ont disparu à l'extraction (cas fréquent
    dans ce corpus : montants de bourses, tarifs, calendrier, contacts).
    Signature : une série de lignes COURTES (les lignes de prose, elles,
    remplissent la largeur ~85-100 caractères), commençant souvent par
    une majuscule ou un chiffre (début de ligne de tableau), avec des
    montants/dates. Ces lignes seront conservées une par ligne au lieu
    d'être fondues en un seul paragraphe illisible."""

    def candidate(i):
        line = lines[i]
        if not line or len(line) > 100 or i in heading_idx:
            return False
        if is_protected_heading(line) or is_list_item(line):
            return False
        if CLOSING_LINE_RE.match(line):
            return False
        if line.endswith(("?", "!", ":", ";")):
            return False
        if line.endswith(".") and not MONTH_ABBR_END_RE.search(line):
            return False
        if uppercase_ratio(line) >= 0.7:
            return False
        return True

    # Séries de candidates ; une ligne vide (saut de page au milieu d'un
    # tableau) ne coupe pas la série si une candidate suit.
    runs, current = [], []
    for i, line in enumerate(lines):
        if candidate(i):
            current.append(i)
        elif not line and current:
            nxt = i + 1
            while nxt < len(lines) and not lines[nxt]:
                nxt += 1
            if nxt >= len(lines) or not candidate(nxt):
                runs.append(current)
                current = []
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)

    table_idx = set()
    for run in runs:
        if len(run) < 3:
            continue
        seg = [lines[i] for i in run]
        digit_ratio = sum(any(c.isdigit() for c in x) for x in seg) / len(seg)
        upper_start = sum(x[0].isupper() or x[0].isdigit() for x in seg) / len(seg)
        median_len = sorted(len(x) for x in seg)[len(seg) // 2]
        numeric_table = digit_ratio >= 0.5 and upper_start >= 0.5
        textual_table = (len(seg) >= 5 and upper_start >= 0.4
                         and median_len <= 70 and digit_ratio >= 0.15)
        if numeric_table or textual_table:
            # Rognage de fin : les 1-2 lignes de PROSE (>= 80 caractères,
            # largeur pleine) qui suivent un tableau ont pu être aspirées
            # dans la série ; elles redeviennent un paragraphe normal.
            while len(run) > 3 and len(lines[run[-1]]) >= 80:
                run.pop()
            table_idx.update(run)
    return table_idx


# ---------------------------------------------------------------------------
# 3. Nettoyage principal
# ---------------------------------------------------------------------------
def clean_text_with_stats(text):
    stats = {
        "mojibake_repare": False,
        "lignes_bruit_supprimees": 0,      # numéros de page, ©, URL isolées...
        "entetes_repetes_supprimes": 0,    # en-têtes/pieds détectés auto
        "cesures_recollees": 0,            # mots coupés en fin de ligne
        "lignes_tableau_preservees": 0,    # lignes de tableaux aplatis
        "pages_detectees": 0,
    }

    # --- 3.0 Préparation ----------------------------------------------------
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    text, stats["mojibake_repare"] = repair_mojibake(text)
    text = normalize_characters(text)
    # En-têtes détectés par position dans les pages (si \f présents)
    positional_header_keys, stats["pages_detectees"] = detect_page_headers(text)
    # Saut de page sur sa propre ligne : servira de frontière de paragraphe.
    text = text.replace(PAGE_MARKER, "\n" + PAGE_MARKER + "\n")

    raw_lines = text.split("\n")
    blank = [ln.strip() == "" or ln.strip() == PAGE_MARKER for ln in raw_lines]

    # --- 3.1 Nettoyage ligne par ligne --------------------------------------
    lines = []
    for i, raw in enumerate(raw_lines):
        line = raw.strip()
        if line == PAGE_MARKER:
            lines.append("")          # frontière de page = ligne vide
            continue
        if not line:
            lines.append("")
            continue

        # En-tête courant avec séparateur "|" :
        # "UNIVERSITÉ DE LA VAKINANKARATRA (UVK)  |  Guide des bourses"
        # (institution en majuscules + titre court). Présent 40 fois dans
        # le corpus, parfois UNE seule fois (documents de 2 pages) : il
        # faut donc le reconnaître à sa forme, pas à sa fréquence. Testé
        # avant la conversion des colonnes en " | " ci-dessous.
        if line.count("|") == 1 and len(line) <= 130:
            left, right = (part.strip() for part in line.split("|", 1))
            if uppercase_ratio(left) >= 0.7 and 1 <= len(right.split()) <= 8:
                stats["lignes_bruit_supprimees"] += 1
                continue

        # Colonnes de tableau aplaties par l'extraction : 3+ espaces / tabs
        if "\t" in line or len(re.findall(r" {3,}", line)) >= 2:
            line = re.sub(r"(\t| {3,})", " | ", line)
        line = re.sub(r" {2,}", " ", line).strip()

        # Sommaires : "Chapitre 1 ............ 12" -> "Chapitre 1"
        line = re.sub(r"(?:\s*[._·]){3,}\s*\d{1,4}\s*$", "", line).strip()

        # Blancs de formulaire : "Je soussigné(e) ..........," -> "... ,"
        line = re.sub(r"\.{4,}", "...", line)

        # Mots collés aux jonctions de colonnes (2027Enseignements...)
        line = repair_glued_words(line)

        # Puce normalisée en début de liste (y compris cases à cocher ☐)
        line = re.sub(r"^[-*+•·☐☑☒✓✔]\s+", "- ", line)

        # Lignes qui ne sont que séparateurs / ponctuation
        if re.fullmatch(r"[-_=*~.·|/\\]{3,}", line) or re.fullmatch(r"[^\w\s]{1,3}", line):
            stats["lignes_bruit_supprimees"] += 1
            lines.append("")
            continue

        low = line.lower()

        # Pied de page du corpus : "Année académique 2026 - 2027 - Page 6"
        if ACADEMIC_YEAR_FOOTER_RE.match(low):
            stats["lignes_bruit_supprimees"] += 1
            continue

        # Numéro de page isolé, toutes formes (uniquement si isolé par des
        # vides / une frontière de page : protège les chiffres de tableaux)
        prev_blank = blank[i - 1] if i > 0 else True
        next_blank = blank[i + 1] if i + 1 < len(raw_lines) else True
        # Forme décorée univoque "- 12 -" : toujours un numéro de page
        if re.fullmatch(r"-\s*\d{1,4}\s*-", line):
            stats["lignes_bruit_supprimees"] += 1
            continue
        if re.fullmatch(r"-?\s*\d{1,4}\s*-?", line) and (prev_blank or next_blank):
            stats["lignes_bruit_supprimees"] += 1
            continue
        if re.fullmatch(r"page\s*\d{1,4}(\s*(sur|/|de)\s*\d{1,4})?", low):
            stats["lignes_bruit_supprimees"] += 1
            continue
        if re.fullmatch(r"\d{1,4}\s*/\s*\d{1,4}", line) and (prev_blank or next_blank):
            stats["lignes_bruit_supprimees"] += 1
            continue

        # Pied de page © / copyright / URL ou e-mail ISOLÉ (jamais inline)
        if len(line) <= 120 and re.match(r"^(©|\(c\)|copyright\b|tous droits)", low):
            stats["lignes_bruit_supprimees"] += 1
            continue
        # URL / e-mail seul sur sa ligne : ce peut être un pied de page,
        # MAIS aussi une vraie donnée (cellule d'un tableau Contacts,
        # comme dans 02 et 05 !). On ne supprime que si le voisinage
        # immédiat confirme un pied de page (numéro de page, ©, en-tête
        # courant, saut de page) ; sinon, on conserve.
        if re.fullmatch(r"(https?://|www\.)\S+", line) or re.fullmatch(r"\S+@\S+\.\S+", line):
            def _is_page_noise(j):
                if j < 0 or j >= len(raw_lines):
                    return False
                neigh = raw_lines[j].strip()
                if neigh == PAGE_MARKER:
                    return True
                nlow = re.sub(r"\s+", " ", neigh.lower().replace("–", "-").replace("—", "-"))
                if (re.fullmatch(r"-?\s*\d{1,4}\s*-?", neigh)
                        or re.fullmatch(r"page\s*\d{1,4}(\s*(sur|/|de)\s*\d{1,4})?", nlow)
                        or ACADEMIC_YEAR_FOOTER_RE.match(nlow)
                        or re.match(r"^(©|\(c\)|copyright\b|tous droits)", nlow)):
                    return True
                if neigh.count("|") == 1:   # en-tête courant voisin
                    return uppercase_ratio(neigh.split("|")[0]) >= 0.7
                return False

            # Voisin DIRECT de bruit de page, ou séparé de lui par la seule
            # ligne vide du changement de page. (À ±2 lignes sans vide, on
            # est simplement en fin de page : c'est du contenu, cf. 05.)
            near_page_noise = False
            for step in (-1, 1):
                j = i + step
                if _is_page_noise(j):
                    near_page_noise = True
                elif 0 <= j < len(raw_lines) and not raw_lines[j].strip() \
                        and _is_page_noise(j + step):
                    near_page_noise = True
            if near_page_noise:
                stats["lignes_bruit_supprimees"] += 1
                continue

        lines.append(line)

    # --- 3.2 Détection auto des en-têtes / pieds répétés --------------------
    # a) Sauts de page présents -> clés positionnelles (déjà calculées).
    # b) Sinon -> méthode prudente : répétition fréquente ET (ligne collée
    #    à une frontière de page = ligne vide autour, OU allure d'en-tête :
    #    majuscules / mots capitalisés). Une ligne de corps de texte
    #    répétée (minuscules, virgules, milieu de paragraphe) est donc
    #    préservée : mieux vaut laisser un peu de bruit que perdre du contenu.
    if positional_header_keys:
        header_keys = positional_header_keys
    else:
        est_pages = stats["pages_detectees"] or max(
            1, round(len(text) / CHARS_PER_PAGE_ESTIMATE))
        threshold = max(MIN_REPETITIONS_ENTETE,
                        int(RATIO_PAGES_ENTETE * est_pages + 0.5))

        def strict_candidate_ok(line):
            if not base_candidate_ok(line):
                return False
            if len(line) > 85 or len(line.split()) > 9:
                return False
            if line[0].islower():
                return False
            # Un vrai tableau converti contient >= 2 séparateurs " | " ;
            # un en-tête "Institution | Titre" n'en contient qu'un.
            if is_table_line(line) and line.count("|") >= 2:
                return False
            if line.endswith((".", ",", ";", "!", "?")):
                return False
            if "," in line or ";" in line or re.search(r"[.!?]\s+\S", line):
                return False
            return True

        occurrences = {}
        for idx, line in enumerate(lines):
            if line and strict_candidate_ok(line):
                occurrences.setdefault(repeated_key(line), []).append(idx)

        header_keys = set()
        for key, idxs in occurrences.items():
            if not key or len(idxs) < threshold:
                continue
            border = sum(
                1 for idx in idxs
                if idx == 0 or not lines[idx - 1]
                or idx + 1 >= len(lines) or not lines[idx + 1])
            sample = lines[idxs[0]]
            if border / len(idxs) >= 0.5 or looks_like_header(sample):
                header_keys.add(key)

    if header_keys:
        # Variantes d'une même clé ("... Page 12" / "... Page 13") : seule
        # la partie stable est gardée, une fois, dans la 1re occurrence.
        variants = {}
        for line in lines:
            if line:
                k = repeated_key(line)
                if k in header_keys:
                    variants.setdefault(k, set()).add(line)

        seen_once = set()
        kept = []
        for line in lines:
            key = repeated_key(line) if line else ""
            if key in header_keys:
                if key in seen_once:      # on garde la 1re occurrence seulement
                    stats["entetes_repetes_supprimes"] += 1
                    continue
                seen_once.add(key)
                if len(variants.get(key, ())) > 1:
                    line = re.sub(
                        r"\s*[-|]\s*page\s*\d+(\s*(sur|/)\s*\d+)?.*$", "",
                        line, flags=re.IGNORECASE).strip()
                    line = re.sub(r"\s+\d{1,3}\s*$", "", line).strip()
                    if not line:
                        stats["entetes_repetes_supprimes"] += 1
                        continue
            kept.append(line)
        lines = kept

    # --- 3.3 Recoller les paragraphes (césures, sauts de ligne au milieu) ---
    # Deux familles d'extraction : si le fichier contient beaucoup de
    # lignes vides, ce sont de vrais paragraphes (extraction Word, 17-20) ;
    # sinon ce sont des lignes visuelles de PDF (01-12) et les rares lignes
    # vides sont surtout des changements de page.
    paragraph_style = bool(lines) and (
        sum(1 for ln in lines if not ln) / len(lines) > 0.25)

    # 1) Titres certains (Article/Chapitre, MAJUSCULES, intro en ":")...
    heading_idx = {i for i, line in enumerate(lines)
                   if line and is_heading_line(line)}
    # 2) ... puis les tableaux aplatis (montants, dates...) : une ligne
    # d'en-tête de tableau ("Étape Dates") ne doit pas être reclassée
    # "petit titre" à l'étape suivante, sinon chaque re-nettoyage
    # détacherait une ligne de plus du tableau.
    table_idx = detect_table_lines(lines, heading_idx)
    stats["lignes_tableau_preservees"] = len(table_idx)

    # 3) ... enfin les petits titres courts heuristiques, hors tableaux.
    nonblank_ordinal = -1
    for i, line in enumerate(lines):
        if not line:
            continue
        nonblank_ordinal += 1
        if i in heading_idx or i in table_idx or is_table_line(line):
            continue
        if CLOSING_LINE_RE.match(line):
            continue   # "Fait à Antsirabe, le 12 septembre" n'est pas un titre
        # Page de garde : les 7 premières lignes courtes (institution,
        # ville, année, titre, sous-titre, référence) restent séparées
        # au lieu d'être fondues les unes dans les autres.
        if (nonblank_ordinal < 7 and len(line) <= 85
                and len(line.split()) <= 13 and not line[0].islower()
                and not line.endswith((".", ",", ";", "!", "?", "-"))):
            heading_idx.add(i)
            continue
        # Extraction par paragraphes : ligne courte isolée entre deux
        # lignes vides ("Présents", "Ordre du jour") = intertitre.
        if paragraph_style and len(line) <= 70 and len(line.split()) <= 10:
            prev_blank = i == 0 or not lines[i - 1]
            next_blank = i + 1 >= len(lines) or not lines[i + 1]
            if (prev_blank and next_blank and not line[0].islower()
                    and not line.endswith((".", ",", ";", "!", "?"))):
                heading_idx.add(i)
                continue
        if len(line) <= 65 and len(line.split()) <= 9 and not line.endswith((".", ",", ";", "!", "?", "-")):
            # Un fragment qui commence par une année ("2027 Enseignements
            # du premier semestre") est une suite de tableau, pas un titre.
            if not line[0].islower() and not re.match(r"\d{4}\b", line):
                prev_blank = i == 0 or not lines[i - 1] or lines[i - 1].endswith((".", "!", "?"))
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                if prev_blank and nxt and not nxt[0].islower():
                    heading_idx.add(i)

    paragraphs = []
    current = ""
    current_is_table = False
    current_is_list = False

    def flush():
        nonlocal current, current_is_table, current_is_list
        if current.strip():
            paragraphs.append(current.strip())
        current = ""
        current_is_table = False
        current_is_list = False

    for i, line in enumerate(lines):
        if not line:
            # Extraction PDF : une ligne vide peut n'être qu'un changement
            # de page au milieu d'une phrase/d'un tableau (en-tête et pied
            # venaient d'être retirés). Si le texte en cours ne se termine
            # pas et que la suite n'est ni un titre ni une liste, on ne
            # coupe pas : la logique de recollement ci-dessous décidera.
            if not paragraph_style and current:
                nxt = i + 1
                while nxt < len(lines) and not lines[nxt]:
                    nxt += 1
                if nxt < len(lines):
                    soft = False
                    if current_is_table and nxt in table_idx:
                        soft = True
                    elif (nxt not in heading_idx
                            and not is_list_item(lines[nxt])
                            and not re.search(r'[.!?;:]["\')\]]?\s*$', current)):
                        soft = True
                    if soft:
                        continue
            flush()
            continue

        if i in heading_idx:
            flush()
            # Titre en MAJUSCULES coupé sur 2 lignes :
            # "RÈGLEMENT DE LA BIBLIOTHÈQUE" + "UNIVERSITAIRE"
            if (paragraphs and uppercase_ratio(line) >= 0.7
                    and uppercase_ratio(paragraphs[-1]) >= 0.7
                    and "\n" not in paragraphs[-1]):
                paragraphs[-1] += " " + line
            else:
                paragraphs.append(line)
            continue

        if is_table_line(line) or i in table_idx:
            if current and current_is_table:
                current += "\n" + line       # lignes d'un tableau : bloc uni
            else:
                flush()
                current, current_is_table = line, True
            continue

        if is_list_item(line):
            flush()
            current = line                    # la suite éventuelle se recolle
            current_is_list = True
            continue

        if not current:
            current = line
            continue

        if current_is_table:
            flush()
            current = line
            continue

        # Mot coupé SANS tiret à la fin d'une ligne pleine : dans ce corpus,
        # "excl" + "usion...", "entr" + "etien...", "co" + "mmission...".
        # Indices sûrs : le fragment de fin se termine par un groupe de
        # consonnes impossible en fin de mot français (consonne + l/r,
        # sans 'e' final), ou le mot suivant commence par une double
        # consonne (aucun mot français ne commence par "mm"...).
        _last = re.search(r"([A-Za-zÀ-ÖØ-öø-ÿ]+)$", current)
        _first = re.match(r"([A-Za-zÀ-ÖØ-öø-ÿ]+)", line)
        if _last and _first:
            _frag, _nxt = _last.group(1), _first.group(1)
            _vowels = "aeiouyàâäéèêëîïôöùûü"
            _double_start = (len(_nxt) >= 2 and _nxt[0] == _nxt[1]
                             and _nxt[0].islower() and _nxt[0] not in _vowels)
            _cluster_end = (len(_frag) <= 5 and _frag.islower()
                            and _frag[-1] in "lr"
                            and _frag[-2] not in _vowels + "lr"
                            and _nxt[0].lower() in _vowels)
            if _double_start or _cluster_end:
                current += line
                stats["cesures_recollees"] += 1
                continue

        # Césure : "informa-" + "tion" -> "information"
        if current.endswith("-") and len(current) >= 2 and current[-2].isalpha() and line[0].isalpha():
            if line[0].islower():
                current = current[:-1] + line
            else:
                current = current + line      # nom composé/propre : garder "-"
            stats["cesures_recollees"] += 1
            continue

        # Montant coupé DANS son premier groupe de chiffres :
        # "... un droit de 1" + "0 000 Ar" -> "... un droit de 10 000 Ar"
        m_cur = re.search(r"(?<!\d)(\d{1,2})$", current)
        m_nxt = re.match(r"(\d{1,2})\s+\d{3}\b", line)
        if m_cur and m_nxt and len(m_cur.group(1)) + len(m_nxt.group(1)) <= 3:
            current += line
            stats["cesures_recollees"] += 1
            continue

        # Après un item de liste COURT sans ponctuation finale, une ligne
        # commençant par une majuscule est une phrase nouvelle, pas la
        # suite de l'item ("- Respecter le silence" / "Le prêt est...").
        if current_is_list and not line[0].islower():
            if len(current) < 55 or current.endswith((".", "!", "?", ":", ";")):
                flush()
                current = line
                continue

        ends_sentence = bool(re.search(r'[.!?]["\')\]]?\s*$', current))
        starts_lower = line[0].islower()
        if not ends_sentence or starts_lower:
            current += " " + line             # même phrase : recoller
        else:
            flush()
            current = line
    flush()

    # --- 3.4 Finitions --------------------------------------------------------
    cleaned_paras = []
    for para in paragraphs:
        para = re.sub(r"[ \t]+", " ", para)
        para = re.sub(r"\s+(,|\.(?!\.))", r"\1", para)  # "mot ." -> "mot." ("..." épargné)
        # « l'UVK » devenu " l'UVK " : retirer les espaces INTÉRIEURES
        # aux guillemets, pas celle qui précède le guillemet ouvrant.
        para = re.sub(r'([\s(])"\s+', r'\1"', para)
        para = re.sub(r'\s+"(?=[\s).,;:!?]|$)', '"', para)
        para = "\n".join(ln.strip() for ln in para.split("\n")).strip()
        if not para:
            continue
        # Paragraphe dupliqué à la suite (artefact d'extraction fréquent)
        if cleaned_paras and cleaned_paras[-1] == para:
            continue
        cleaned_paras.append(para)

    cleaned = "\n\n".join(cleaned_paras).strip()
    return cleaned, stats


def clean_text(text):
    """Compatibilité avec le script d'origine : renvoie le texte nettoyé."""
    cleaned, _ = clean_text_with_stats(text)
    return cleaned


# ---------------------------------------------------------------------------
# 4. Lecture / recherche des fichiers
# ---------------------------------------------------------------------------
def read_text_file(path):
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace"), "latin-1?"


def collect_files(input_dir, exclude_dir=None):
    files = []
    exclude = exclude_dir.resolve() if exclude_dir else None
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        if BACKUP_DIR_NAME in path.parts or path.name.startswith("."):
            continue
        if exclude and exclude in path.resolve().parents:
            continue
        files.append(path)
    return files


def find_input_dir(explicit=None):
    bases = []
    for base in (Path.cwd(), Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 2 else Path.cwd()):
        if base not in bases:
            bases.append(base)

    if explicit:
        for base in bases:
            cand = Path(explicit) if Path(explicit).is_absolute() else base / explicit
            if cand.is_dir():
                return cand, bases
        return None, bases

    found = []
    for base in bases:
        for rel in CANDIDATE_INPUT_DIRS:
            cand = base / rel
            if cand.is_dir() and collect_files(cand):
                found.append(cand)
    # garder l'ordre de priorité, sans doublons
    ordered = []
    for rel in CANDIDATE_INPUT_DIRS:
        for cand in found:
            if cand.as_posix().endswith(rel) and cand not in ordered:
                ordered.append(cand)
    return (ordered[0] if ordered else None), bases


def default_output_dir(input_dir, in_place_flag):
    if in_place_flag or input_dir.name == "processed":
        return input_dir, True
    # raw et processed restent dans la MÊME arborescence que l'entrée :
    # doc_rag/raw -> doc_rag/processed ; data/raw -> data/processed
    if input_dir.name == "raw" and input_dir.parent.name in ("doc_rag", "data"):
        return input_dir.parent / "processed", False
    return input_dir.parent / "data" / "processed", False


# ---------------------------------------------------------------------------
# 5. Programme principal
# ---------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Nettoie les textes extraits pour le RAG.")
    parser.add_argument("input", nargs="?", default=None,
                        help="dossier contenant les .txt extraits (optionnel : détection auto sinon)")
    parser.add_argument("--output", default=None,
                        help="dossier de sortie (optionnel : data/processed ou sur place selon l'entrée)")
    parser.add_argument("--in-place", action="store_true",
                        help="forcer le nettoyage sur place (avec backup)")
    args = parser.parse_args(argv)

    input_dir, bases = find_input_dir(args.input)
    if input_dir is None:
        print("❌ Aucun dossier d'entrée trouvé contenant des .txt / .md.")
        print("   Cherché (depuis " + ", ".join(str(b) for b in bases) + ") :")
        for rel in CANDIDATE_INPUT_DIRS:
            print(f"     - {rel}/")
        print("   Lance d'abord extract.py, ou précise : python src/ingestion/clean.py doc_rag/processed")
        return 1

    input_dir = input_dir.resolve()
    if args.output:
        out_path = Path(args.output)
        output_dir = (out_path if out_path.is_absolute() else Path.cwd() / out_path).resolve()
        in_place = output_dir == input_dir
    else:
        output_dir, in_place = default_output_dir(input_dir, args.in_place)
        output_dir = output_dir.resolve()

    files = collect_files(input_dir, exclude_dir=None if in_place else output_dir)
    if not files:
        print(f"❌ Aucun fichier .txt / .md dans : {input_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = input_dir / BACKUP_DIR_NAME if in_place else None

    print(f"📥 Entrée  : {input_dir}  ({len(files)} fichier(s))")
    print(f"📤 Sortie  : {output_dir}" + ("  (sur place, avec backup)" if in_place else ""))
    if backup_dir:
        print(f"💾 Backup   : {backup_dir} (jamais écrasé)")
    print()

    report = {"input_dir": str(input_dir), "output_dir": str(output_dir), "files": []}
    ok, errors = 0, 0

    for filepath in files:
        rel = filepath.relative_to(input_dir)
        try:
            original, enc = read_text_file(filepath)
            cleaned, stats = clean_text_with_stats(original)

            if backup_dir:
                backup_path = backup_dir / rel
                if not backup_path.exists():
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(filepath, backup_path)

            out_file = output_dir / rel
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(cleaned, encoding="utf-8")

            before, after = len(original), len(cleaned)
            pct = ((before - after) / before * 100) if before else 0.0
            signe = f"-{pct:.1f}%" if pct >= 0 else f"+{-pct:.1f}%"
            print(f"✅ {rel} : {before} → {after} caractères ({signe} de bruit)")
            notes = []
            if stats["mojibake_repare"]:
                notes.append("encodage Ã© réparé")
            if stats["lignes_bruit_supprimees"]:
                notes.append(f"{stats['lignes_bruit_supprimees']} ligne(s) de bruit retirée(s) "
                             "(en-têtes/pieds/numéros de page)")
            if stats["entetes_repetes_supprimes"]:
                notes.append(f"{stats['entetes_repetes_supprimes']} en-têtes/pieds répétés retirés")
            if stats["cesures_recollees"]:
                notes.append(f"{stats['cesures_recollees']} césure(s) recollée(s)")
            if stats["lignes_tableau_preservees"]:
                notes.append(f"{stats['lignes_tableau_preservees']} ligne(s) de tableau préservée(s)")
            if after < 500:
                notes.append("⚠️ moins de 500 caractères : PDF scan/image possible, à vérifier")
            if pct > 40:
                notes.append("⚠️ réduction > 40% : vérifier manuellement qu'on n'a pas trop supprimé")
            if pct < 0:
                notes.append("texte légèrement allongé (réparations) : normal si l'extraction était déjà propre")
            if notes:
                print("   " + " ; ".join(notes))

            report["files"].append({
                "file": str(rel), "encoding_lu": enc,
                "chars_avant": before, "chars_apres": after,
                "reduction_pct": round(pct, 1), **stats,
            })
            ok += 1
        except Exception as e:
            print(f"❌ {rel} : {e}")
            errors += 1

    try:
        (output_dir / REPORT_NAME).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    print(f"\n🧹 Nettoyage terminé ! {ok}/{len(files)} fichier(s) OK"
          + (f", {errors} erreur(s)" if errors else ""))
    print(f"📁 Textes propres dans : {output_dir}")
    print("👉 Vérifie à l'œil 2-3 fichiers (étape 3.5), puis lance chunk.py.")
    if output_dir.name != "processed":
        print("⚠️ La sortie n'est pas data/processed : adapte PROCESSED_DIR dans chunk.py "
              f"-> {output_dir}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
