"""
Stockage en mémoire des documents et de leurs segments.
Suffisant pour le prototype. À remplacer par SQLite si nécessaire.
"""

# Dictionnaire global qui contient tous les documents uploadés
# Structure :
# {
#     "reglement": {
#         "nom_fichier": "reglement",
#         "nom_original": "reglement.pdf",
#         "nombre_pages": 12,
#         "nombre_segments": 45,
#         "segments": [
#             {"segment_id": 1, "nom_fichier": "reglement", "page": 1, "texte": "..."},
#             ...
#         ]
#     },
#     ...
# }
documents = {}


def ajouter_document(nom_fichier, nom_original, nombre_pages, segments):
    """
    Ajoute un document et ses segments dans le stockage.
    """
    documents[nom_fichier] = {
        "nom_fichier": nom_fichier,
        "nom_original": nom_original,
        "nombre_pages": nombre_pages,
        "nombre_segments": len(segments),
        "segments": segments
    }


def obtenir_document(nom_fichier):
    """
    Récupère un document par son nom.
    Retourne None si le document n'existe pas.
    """
    return documents.get(nom_fichier)


def obtenir_tous_les_documents():
    """
    Récupère la liste de tous les documents (sans les segments, pour alléger).
    """
    resultat = []
    for nom, doc in documents.items():
        resultat.append({
            "nom_fichier": doc["nom_fichier"],
            "nom_original": doc["nom_original"],
            "nombre_pages": doc["nombre_pages"],
            "nombre_segments": doc["nombre_segments"]
        })
    return resultat


def obtenir_tous_les_segments():
    """
    Récupère tous les segments de tous les documents.
    Utile pour A1 quand il devra construire l'index vectoriel.
    """
    tous = []
    for doc in documents.values():
        tous.extend(doc["segments"])
    return tous