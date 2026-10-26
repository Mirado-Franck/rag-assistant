#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chunk.py — Découpage des textes nettoyés en chunks pour le RAG (Partie 4).

Version adaptée au corpus UVK (sortie de clean.py dans doc_rag/processed/).

POURQUOI PAS LE DÉCOUPAGE "AU COMPTEUR" DE LA CONSIGNE ?
---------------------------------------------------------
Le script de base coupe tous les CHUNK_SIZE caractères, puis repart
CHUNK_OVERLAP caractères en arrière pour le chunk suivant. Résultat
constaté sur ce corpus :
  - chunks qui commencent au milieu d'un mot ("e, les droits...",
    "n accepte les dispositions...") ;
  - chunks qui se terminent sur un début de titre ("... Article 5.") ;
  - augmenter CHUNK_OVERLAP à 100 empire même le phénomène.

STRATÉGIE UTILISÉE ICI : on découpe sur la STRUCTURE du texte.
----------------------------------------------------------------
clean.py produit des blocs séparés par des lignes vides : titres
(TITRE..., Article X, 1. Section...), paragraphes, puces, tableaux
(blocs multi-lignes). Ce script assemble ces blocs entiers jusqu'à
atteindre la taille visée, avec quatre règles d'or :
  1. Jamais de coupure au milieu d'un mot ni d'une phrase ; un
     paragraphe trop long est coupé entre ses phrases (détection
     adaptée au français : abréviations, "M.", "art." etc.).
  2. Jamais de titre orphelin : un titre n'est jamais la dernière
     chose d'un chunk, et une ligne d'introduction ("... suivants :")
     reste collée à ce qu'elle annonce.
  3. L'overlap répète la DERNIÈRE PHRASE ENTIÈRE du chunk précédent
     (environ CHUNK_OVERLAP caractères, arrondi à la phrase), jamais
     un bout de mot. Au changement de section/article, pas d'overlap :
     c'est le titre qui sert de contexte.
  4. Un tableau trop long est coupé ENTRE ses lignes, et sa ligne
     d'en-tête est répétée en haut du morceau suivant ; idem pour
     une longue liste à puces coupée en deux : sa phrase
     d'introduction ("... les pièces suivantes :") est répétée.

Chaque chunk garde les métadonnées attendues par la suite du projet
(id, source, chunk_index, text, char_count) + un champ "section"
(ex : "TITRE II - ... > Article 5. - ...") utile pour les citations.

UTILISATION
-----------
    python src/ingestion/chunk.py
Le script cherche les .txt nettoyés dans doc_rag/processed/, puis
data/processed/ (jamais dans _backup_avant_nettoyage/), et écrit
all_chunks.json dans le dossier chunks/ voisin (doc_rag/chunks/ ou
data/chunks/ selon l'entrée trouvée).
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paramètres (étape 4.3 : ajuste-les si les chunks ne te plaisent pas)
# ---------------------------------------------------------------------------
CHUNK_SIZE = 600        # taille visée d'un chunk (caractères)
CHUNK_MAX = 800         # taille max (souple : un titre + son paragraphe
                        # peuvent dépasser légèrement, plutôt que d'être
                        # séparés)
CHUNK_MIN = 200         # en dessous, on fusionne avec le chunk voisin
CHUNK_OVERLAP = 100     # chevauchement visé, TOUJOURS arrondi à la
                        # dernière phrase entière (voir règle 3)

# À partir de quelle longueur de chunk en cours un nouveau titre
# (Article / section numérotée / question FAQ) déclenche un nouveau
# chunk ? Évite les micro-chunks "article de 2 lignes" tout en
# gardant les articles majoritairement entiers.
FLUSH_AT_HEADING = 280
FLUSH_AT_MAJOR_HEADING = 150    # TITRE / CHAPITRE : seuil plus bas

INPUT_CANDIDATES = ("doc_rag/processed", "data/processed", "processed")
BACKUP_DIR_NAME = "_backup_avant_nettoyage"

# ---------------------------------------------------------------------------
# 1. Classification des blocs produits par clean.py
# ---------------------------------------------------------------------------
MAJOR_HEADING_RE = re.compile(
    r"^(TITRE|CHAPITRE|PARTIE|LIVRE|PR[ÉE]AMBULE|ANNEXE)\b", re.IGNORECASE)
ARTICLE_RE = re.compile(r"^(Article|Art\.|Section|§)\b", re.IGNORECASE)
# "4. Calendrier..." ET sous-sections "2.2 Engagements...", "3.3 Procédure..."
NUMBERED_RE = re.compile(r"^\d{1,2}[.)]\s+\S|^\d{1,2}(?:\.\d{1,2})+\s+\S")
LIST_RE = re.compile(r"^([-*•☐]|\d{1,2}[.)])\s")


def uppercase_ratio(text):
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 3:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def classify_block(block):
    """Retourne le type d'un bloc : h1, h2, table, list ou body."""
    lines = [ln for ln in block.split("\n") if ln.strip()]
    # Bloc multi-lignes = tableau aplati conservé par clean.py
    if len(lines) >= 3:
        return "table"
    text = " ".join(lines).strip()
    words = text.split()

    if MAJOR_HEADING_RE.match(text):
        return "h1"
    # Ligne presque entièrement en majuscules = grand titre
    # ("PRÉAMBULE", "RÈGLEMENT INTÉRIEUR GÉNÉRAL"...)
    if len(text) <= 90 and uppercase_ratio(text) >= 0.8:
        return "h1"
    if ARTICLE_RE.match(text):
        return "h2"
    # Question de FAQ = titre de sa réponse
    if text.endswith("?") and len(text) <= 110:
        return "h2"
    # Section numérotée courte ("4. Calendrier de la campagne 2026-2027")
    if (NUMBERED_RE.match(text) and len(text) <= 90 and len(words) <= 12
            and not text.endswith((";", ","))):
        return "h2"
    if LIST_RE.match(text):
        return "list"
    # Petit titre sans numérotation ("Présents", "Ordre du jour",
    # "Antsirabe - Madagascar"...) : court, sans ponctuation de phrase.
    if (len(text) <= 70 and len(words) <= 10 and text[:1].isupper()
            and not text.endswith((".", ",", ";", "!", "?", ")"))
            and "..." not in text and "@" not in text):
        return "h2"
    return "body"


# ---------------------------------------------------------------------------
# 2. Découpage fin : phrases françaises, lignes de tableau, mots
# ---------------------------------------------------------------------------
# Abréviations dont le point NE termine PAS une phrase.
_ABBREV = ["M.", "Mme.", "Mlle.", "Dr.", "Pr.", "Me.", "art.", "Art.",
           "cf.", "etc.", "ex.", "p.", "vol.", "n°", "N°", "St.", "Ste.",
           "av.", "apr.", "env.", "min.", "max."]
_PLACEHOLDER = "\x00"
_SENT_BOUNDARY_RE = re.compile(
    r"([.!?…]+[\"»)]?)\s+(?=[A-ZÀ-ÖØ-Þ«\"(0-9])")


def split_sentences(text):
    """Découpe un paragraphe en phrases (sans casser les abréviations)."""
    protected = text
    for abbr in _ABBREV:
        protected = protected.replace(abbr, abbr.replace(".", _PLACEHOLDER))
    # Nombres décimaux et initiales ("7.5", "J. Rakoto")
    protected = re.sub(r"(\d)\.(\d)", r"\1" + _PLACEHOLDER + r"\2", protected)
    protected = re.sub(r"\b([A-ZÀ-Þ])\.(?=\s+[A-ZÀ-Þ])",
                       r"\1" + _PLACEHOLDER, protected)
    marked = _SENT_BOUNDARY_RE.sub(r"\1\n", protected)
    sentences = []
    for piece in marked.split("\n"):
        piece = piece.replace(_PLACEHOLDER, ".").strip()
        if piece:
            sentences.append(piece)
    return sentences or [text.strip()]


def split_by_words(text, max_len):
    """Dernier recours : coupe entre les mots (JAMAIS à l'intérieur)."""
    parts, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_len:
            parts.append(current)
            current = word
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def split_long_text(text, max_len):
    """Découpe un texte trop long en morceaux <= max_len, par phrases."""
    pieces, current = [], ""
    for sentence in split_sentences(text):
        if len(sentence) > max_len:
            if current:
                pieces.append(current)
                current = ""
            # Phrase géante : couper aux ';' / ',' puis aux mots
            clauses = re.split(r"(?<=[;,])\s+", sentence)
            for clause in clauses:
                if len(clause) > max_len:
                    pieces.extend(split_by_words(clause, max_len))
                elif current and len(current) + 1 + len(clause) > max_len:
                    pieces.append(current)
                    current = clause
                else:
                    current = f"{current} {clause}".strip()
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_len:
            pieces.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def split_table(block, max_len):
    """Coupe un tableau entre ses lignes, en-tête répété à chaque morceau."""
    rows = [ln.strip() for ln in block.split("\n") if ln.strip()]
    header, body_rows = rows[0], rows[1:]
    pieces, current = [], header
    for row in body_rows:
        candidate = f"{current}\n{row}"
        if len(candidate) > max_len and current != header:
            pieces.append(current)
            current = f"{header}\n{row}"   # on répète l'en-tête (règle 4)
        else:
            current = candidate
    pieces.append(current)
    return pieces


def last_sentences(text, max_chars):
    """Dernière(s) phrase(s) entière(s) d'un texte, pour l'overlap."""
    last_block = text.split("\n\n")[-1]
    if "\n" in last_block:            # se termine par un tableau : pas
        return ""                      # d'overlap (l'en-tête répété suffit)
    sentences = split_sentences(last_block)
    picked, total = [], 0
    for sentence in reversed(sentences):
        # Une phrase seule peut dépasser un peu la cible : mieux vaut
        # une phrase entière de 160 car. qu'un bout de mot de 100.
        if picked and total + len(sentence) > max_chars:
            break
        if not picked and len(sentence) > 2 * max_chars:
            return ""
        picked.insert(0, sentence)
        total += len(sentence)
        if total >= max_chars:
            break
    return " ".join(picked)


# ---------------------------------------------------------------------------
# 3. Assemblage des chunks
# ---------------------------------------------------------------------------
def split_into_chunks(text):
    """Découpe un texte nettoyé. Retourne [(texte_du_chunk, section)]."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

    # --- Morceaux atomiques : aucun ne dépasse CHUNK_MAX ----------------
    pieces = []                        # (type, texte)
    for block in blocks:
        kind = classify_block(block)
        if kind == "table":
            if len(block) > CHUNK_MAX:
                pieces.extend(("table", p) for p in split_table(block, CHUNK_MAX))
            else:
                pieces.append(("table", block))
        elif kind in ("body", "list") and len(block) > CHUNK_MAX:
            pieces.extend((kind, p) for p in split_long_text(block, CHUNK_MAX))
        else:
            pieces.append((kind, " ".join(block.split("\n")) if kind != "table"
                           else block))

    # --- Assemblage glouton avec règles d'or ----------------------------
    chunks = []                        # (texte, section)
    current = []                       # morceaux du chunk en cours
    current_len = 0
    section1 = section2 = ""           # titres courants (contexte)
    chunk_section = ""                 # section du chunk en cours
    overlap_seed = ""                  # phrase(s) à recopier au début
    context_seed = ""                  # titre de section à rappeler
    list_seed = ""                     # intro ("... suivants :") à répéter
    list_intro = ""                    # intro de la liste en cours

    def flush(reason):
        nonlocal current, current_len, overlap_seed, context_seed, list_seed
        if not current:
            return
        chunk_text = "\n\n".join(t for _, t in current).strip()
        chunks.append((chunk_text, chunk_section))
        # Prépare le début du chunk suivant (règle 3)
        overlap_seed = context_seed = list_seed = ""
        if reason == "size":
            if current[-1][0] == "list":
                # Fini par une liste : recopier la dernière puce ne
                # servirait à rien. Si la liste continue, on répètera
                # son intro (comme l'en-tête d'un tableau) ; sinon,
                # on rappellera le titre de la section.
                if len(list_intro) <= 250:
                    list_seed = list_intro
                context_seed = section2 or section1
            else:
                overlap_seed = last_sentences(chunk_text, CHUNK_OVERLAP)
                if not overlap_seed:
                    context_seed = section2 or section1
        current, current_len = [], 0

    def current_is_open():
        """Vrai si finir ici laisserait un titre/intro orphelin."""
        kind, txt = current[-1]
        return kind in ("h1", "h2") or txt.rstrip().endswith(":")

    for kind, txt in pieces:
        if current:
            # --- Faut-il fermer le chunk avant ce morceau ? -------------
            if kind == "h1" and current_len >= FLUSH_AT_MAJOR_HEADING \
                    and not current_is_open():
                flush("heading")
            elif kind == "h2" and current_len >= FLUSH_AT_HEADING \
                    and not current_is_open():
                flush("heading")
            elif not current_is_open():
                over_max = current_len + len(txt) > CHUNK_MAX
                over_target = current_len >= CHUNK_SIZE
                # Une liste en cours ("- ... ;") reste groupée tant
                # qu'on ne dépasse pas le maximum.
                in_list = current[-1][0] == "list" and kind == "list"
                if over_max or (over_target and not in_list):
                    flush("size")

        # --- Début d'un nouveau chunk : graine de contexte --------------
        if not current:
            if kind == "h1":
                section1, section2 = txt, ""
            elif kind == "h2":
                section2 = txt
            if kind == "list" and list_seed:
                current.append(("body", list_seed))
                current_len += len(list_seed) + 2
            elif overlap_seed and kind not in ("h1", "h2"):
                current.append(("overlap", overlap_seed))
                current_len += len(overlap_seed) + 2
            elif context_seed and kind in ("body", "list", "table"):
                current.append(("h2", context_seed))
                current_len += len(context_seed) + 2
            overlap_seed = context_seed = list_seed = ""
            chunk_section = " > ".join(
                s for s in (section1, section2) if s)
            if kind == "h1":
                chunk_section = section1
            elif kind == "h2":
                chunk_section = " > ".join(
                    s for s in (section1, section2) if s)
        else:
            # Titre au milieu d'un chunk : il met à jour le contexte
            # pour les chunks suivants.
            if kind == "h1":
                section1, section2 = txt, ""
            elif kind == "h2":
                section2 = txt

        current.append((kind, txt))
        current_len += len(txt) + 2

        # Retient la phrase qui annonce la liste en cours
        # ("... les pièces suivantes :"), pour pouvoir la répéter
        # si la liste doit être coupée entre deux chunks.
        if kind != "list":
            list_intro = txt if (txt.rstrip().endswith(":")
                                 or kind in ("h1", "h2")) else ""

    flush("end")

    # --- Fusion des chunks trop petits et nettoyage final ---------------
    merged = []
    for chunk_text, section in chunks:
        if merged and len(chunk_text) < CHUNK_MIN:
            prev_text, prev_section = merged[-1]
            merged[-1] = (f"{prev_text}\n\n{chunk_text}", prev_section)
        else:
            merged.append((chunk_text, section))
    if len(merged) >= 2 and len(merged[0][0]) < CHUNK_MIN:
        # Premier chunk minuscule (page de garde seule) : vers le suivant
        (t0, _), (t1, s1) = merged[0], merged[1]
        merged[1] = (f"{t0}\n\n{t1}", s1)
        merged.pop(0)

    return [(t, s) for t, s in merged
            if len(t) >= 50 and any(c.isalpha() for c in t)]


# ---------------------------------------------------------------------------
# 4. Recherche des fichiers et programme principal
# ---------------------------------------------------------------------------
def find_input_dir(explicit=None):
    if explicit:
        path = Path(explicit)
        return path if path.is_dir() else None
    roots = [Path.cwd(), Path(__file__).resolve().parents[2]]
    for root in roots:
        for candidate in INPUT_CANDIDATES:
            path = root / candidate
            if path.is_dir() and any(path.glob("*.txt")):
                return path
    return None


def quality_report(all_chunks):
    """Contrôles de l'étape 4.3, automatisés."""
    sizes = [c["char_count"] for c in all_chunks]
    starts_lower = sum(
        1 for c in all_chunks if c["text"][:1].islower())
    last_ids = {}
    for c in all_chunks:               # dernier chunk de chaque fichier
        last_ids[c["source"]] = c["id"]  # (un document peut légitimement
    dangling = sum(                      #  finir sur une signature)
        1 for c in all_chunks
        if c["id"] != last_ids[c["source"]]
        and (classify_block(c["text"].split("\n\n")[-1]) in ("h1", "h2")
             or c["text"].rstrip().endswith(":")))
    tiny = sum(1 for c in all_chunks if c["char_count"] < CHUNK_MIN)
    print("\n🔍 Contrôle qualité automatique (étape 4.3) :")
    print(f"   - tailles : min {min(sizes)} / max {max(sizes)} caractères")
    print(f"   - chunks commençant par une minuscule "
          f"(mot coupé ?) : {starts_lower}")
    print(f"   - chunks finissant sur un titre/intro seul : {dangling}")
    print(f"   - chunks < {CHUNK_MIN} caractères : {tiny}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Découpe les textes nettoyés en chunks (Partie 4).")
    parser.add_argument("input", nargs="?",
                        help="dossier des .txt nettoyés (optionnel)")
    parser.add_argument("-o", "--output",
                        help="fichier JSON de sortie (optionnel)")
    parser.add_argument("--size", type=int, default=None,
                        help="taille visée d'un chunk (défaut 600)")
    parser.add_argument("--overlap", type=int, default=None,
                        help="chevauchement visé en caractères (défaut 100)")
    args = parser.parse_args(argv)

    global CHUNK_SIZE, CHUNK_MAX, CHUNK_OVERLAP
    if args.size:
        CHUNK_SIZE = args.size
        CHUNK_MAX = int(args.size * 1.35)
    if args.overlap is not None:
        CHUNK_OVERLAP = args.overlap

    input_dir = find_input_dir(args.input)
    if input_dir is None:
        print("❌ Aucun dossier de textes nettoyés trouvé "
              f"({', '.join(INPUT_CANDIDATES)}).")
        print("   Lance d'abord clean.py, ou précise : "
              "python src/ingestion/chunk.py doc_rag/processed")
        return 1

    output_path = (Path(args.output) if args.output
                   else input_dir.parent / "chunks" / "all_chunks.json")

    # Uniquement le niveau supérieur : on ne lira JAMAIS les originaux
    # de _backup_avant_nettoyage/.
    files = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".txt", ".md")
        and not p.name.startswith((".", "_"))
        and BACKUP_DIR_NAME not in p.parts)

    print(f"📥 Entrée : {input_dir}  ({len(files)} fichier(s))")

    all_chunks = []
    for filepath in files:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        chunks = split_into_chunks(text)
        for i, (chunk_text, section) in enumerate(chunks):
            all_chunks.append({
                "id": f"{filepath.name}_chunk_{i}",
                "source": filepath.name,
                "chunk_index": i,
                "section": section,
                "text": chunk_text,
                "char_count": len(chunk_text),
            })
        print(f"✅ {filepath.name} : {len(text)} caractères → "
              f"{len(chunks)} chunks")

    if not all_chunks:
        print("❌ Aucun chunk produit.")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    total = len(all_chunks)
    print(f"\n{'=' * 50}")
    print(f"📊 Total : {total} chunks")
    print(f"📁 Sauvegardé dans : {output_path}")
    print(f"📏 Taille moyenne d'un chunk : "
          f"{sum(c['char_count'] for c in all_chunks) // total} caractères")

    quality_report(all_chunks)

    print("\n👀 Aperçu — 3 chunks du premier document :")
    for chunk in all_chunks[:3]:
        print(f"\n--- {chunk['id']} | section : {chunk['section'] or '-'} "
              f"| {chunk['char_count']} car. ---")
        print(chunk["text"][:400])
    print("\n👉 Vérifie à l'œil 5-10 chunks dans all_chunks.json "
          "(étape 4.3), puis passe aux embeddings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
