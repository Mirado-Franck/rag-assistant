from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil

from app.extraction import extraire_texte, obtenir_nom_fichier
from app.decoupage import decouper_document
from app.stockage import ajouter_document, obtenir_document

router = APIRouter()

# Dossier où les fichiers uploadés sont sauvegardés
DOSSIER_UPLOADS = "uploads"

# S'assurer que le dossier existe
os.makedirs(DOSSIER_UPLOADS, exist_ok=True)


@router.post("/upload")
async def upload_document(fichier: UploadFile = File(...)):
    """
    Reçoit un fichier PDF, l'extrait, le découpe et le stocke.
    """

    # --- Vérification 1 : c'est bien un PDF ---
    if not fichier.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers PDF sont acceptés."
        )

    # --- Vérification 2 : le fichier n'est pas vide ---
    if not fichier.filename:
        raise HTTPException(
            status_code=400,
            detail="Le fichier n'a pas de nom."
        )

    # --- Étape 1 : Sauvegarder le fichier ---
    chemin_fichier = os.path.join(DOSSIER_UPLOADS, fichier.filename)

    try:
        with open(chemin_fichier, "wb") as buffer:
            shutil.copyfileobj(fichier.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la sauvegarde du fichier : {e}"
        )

    # --- Étape 2 : Extraire le texte ---
    pages = extraire_texte(chemin_fichier)

    if not pages:
        # Supprimer le fichier s'il est inutilisable
        os.remove(chemin_fichier)
        raise HTTPException(
            status_code=422,
            detail="Impossible d'extraire le texte du PDF. Le fichier est peut-être vide ou corrompu."
        )

    # --- Étape 3 : Découper en segments ---
    nom = obtenir_nom_fichier(fichier.filename)
    segments = decouper_document(pages, nom, taille_segment=500, chevauchement=100)

    if not segments:
        os.remove(chemin_fichier)
        raise HTTPException(
            status_code=422,
            detail="Le PDF ne contient aucun texte exploitable (peut-être un scan image)."
        )

    # --- Étape 4 : Stocker en mémoire ---
    ajouter_document(
        nom_fichier=nom,
        nom_original=fichier.filename,
        nombre_pages=len(pages),
        segments=segments
    )

    # --- Étape 5 : Retourner le résumé ---
    return {
        "message": "Document uploadé et traité avec succès.",
        "nom_fichier": nom,
        "nom_original": fichier.filename,
        "nombre_pages": len(pages),
        "nombre_segments": len(segments)
    }