def decouper_texte(texte, taille_segment=500, chevauchement=100):
    """
    Découpe un texte en segments de taille fixe avec chevauchement.

    Paramètres :
        texte : le texte à découper
        taille_segment : nombre maximum de caractères par segment (défaut 500)
        chevauchement : nombre de caractères communs entre deux segments (défaut 100)

    Retourne :
        Une liste de chaînes de caractères (les segments)
    """

    # Si le texte est vide ou trop court, on le retourne tel quel
    if not texte or len(texte.strip()) == 0:
        return []

    if len(texte) <= taille_segment:
        return [texte.strip()]

    segments = []
    debut = 0

    while debut < len(texte):
        fin = debut + taille_segment
        segment = texte[debut:fin].strip()

        # On n'ajoute pas les segments vides
        if segment:
            segments.append(segment)

        # On avance de (taille - chevauchement) pour créer le recouvrement
        pas = taille_segment - chevauchement
        debut += pas

        # Sécurité : si le pas est trop petit, on avance au moins d'un caractère
        if pas <= 0:
            debut += 1

    return segments


def decouper_document(pages, nom_fichier, taille_segment=500, chevauchement=100):
    """
    Découpe toutes les pages d'un document en segments avec métadonnées.

    Paramètres :
        pages : liste de dictionnaires [{"page": 1, "texte": "..."}, ...]
                (c'est le résultat de la fonction extraire_texte)
        nom_fichier : nom du document source
        taille_segment : taille de chaque segment
        chevauchement : chevauchement entre segments

    Retourne :
        Une liste de dictionnaires :
        [
            {
                "segment_id": 1,
                "nom_fichier": "reglement",
                "page": 1,
                "texte": "Le passage du texte...",
            },
            ...
        ]
    """

    tous_les_segments = []
    compteur = 1

    for page in pages:
        numero_page = page["page"]
        texte = page["texte"]

        # On ne découpe pas les pages vides
        if not texte.strip():
            continue

        segments = decouper_texte(texte, taille_segment, chevauchement)

        for segment in segments:
            tous_les_segments.append({
                "segment_id": compteur,
                "nom_fichier": nom_fichier,
                "page": numero_page,
                "texte": segment
            })
            compteur += 1

    return tous_les_segments