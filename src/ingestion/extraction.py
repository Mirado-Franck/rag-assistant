import fitz
import os


def extraire_texte(chemin_pdf):
    """
    Extrait le texte d'un PDF page par page.

    Paramètre :
        chemin_pdf : chemin vers le fichier PDF

    Retourne :
        Une liste de dictionnaires, un par page :
        [
            {"page": 1, "texte": "..."},
            {"page": 2, "texte": "..."},
            ...
        ]
        Retourne une liste vide si le PDF est invalide.
    """

    # Vérifier que le fichier existe
    if not os.path.exists(chemin_pdf):
        print(f"ERREUR : le fichier '{chemin_pdf}' n'existe pas.")
        return []

    # Vérifier que c'est bien un PDF
    if not chemin_pdf.lower().endswith(".pdf"):
        print(f"ERREUR : le fichier '{chemin_pdf}' n'est pas un PDF.")
        return []

    # Ouvrir le PDF
    try:
        doc = fitz.open(chemin_pdf)
    except Exception as e:
        print(f"ERREUR : impossible d'ouvrir le PDF. {e}")
        return []

    # Vérifier qu'il n'est pas vide
    if doc.page_count == 0:
        print("ERREUR : le PDF ne contient aucune page.")
        doc.close()
        return []

    # Extraire le texte page par page
    resultat = []
    for numero_page in range(doc.page_count):
        page = doc[numero_page]
        texte = page.get_text().strip()
        resultat.append({
            "page": numero_page + 1,
            "texte": texte
        })

    doc.close()
    return resultat


def obtenir_nom_fichier(chemin_pdf):
    """
    Extrait le nom du fichier sans le chemin ni l'extension.
    Exemple : 'documents/reglement.pdf' -> 'reglement'
    """
    return os.path.splitext(os.path.basename(chemin_pdf))[0]