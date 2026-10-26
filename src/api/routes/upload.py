from pathlib import Path
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.api.stockage import ajouter_document
from src.ingestion.decoupage import decouper_document
from src.ingestion.extract import extraire_texte, obtenir_nom_fichier

router = APIRouter()

# Les fichiers reçus sont conservés parmi les données brutes du projet.
RACINE_PROJET = Path(__file__).resolve().parents[3]
DOSSIER_UPLOADS = RACINE_PROJET / "data" / "raw" / "uploads"
DOSSIER_UPLOADS.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_document(fichier: UploadFile = File(...)):
    """Reçoit un fichier PDF, l'extrait, le découpe et le stocke."""

    if not fichier.filename:
        raise HTTPException(status_code=400, detail="Le fichier n'a pas de nom.")

    # Ne conserve que le nom de base pour empêcher toute sortie de data/raw/uploads.
    nom_original = Path(fichier.filename.replace(chr(92), "/")).name
    if not nom_original.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers PDF sont acceptés.",
        )

    chemin_fichier = DOSSIER_UPLOADS / nom_original

    try:
        with chemin_fichier.open("wb") as buffer:
            shutil.copyfileobj(fichier.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la sauvegarde du fichier : {e}",
        )

    pages = extraire_texte(str(chemin_fichier))

    if not pages:
        chemin_fichier.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=(
                "Impossible d'extraire le texte du PDF. "
                "Le fichier est peut-être vide ou corrompu."
            ),
        )

    nom = obtenir_nom_fichier(nom_original)
    segments = decouper_document(pages, nom, taille_segment=500, chevauchement=100)

    if not segments:
        chemin_fichier.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=(
                "Le PDF ne contient aucun texte exploitable "
                "(peut-être un scan image)."
            ),
        )

    ajouter_document(
        nom_fichier=nom,
        nom_original=nom_original,
        nombre_pages=len(pages),
        segments=segments,
    )

    return {
        "message": "Document uploadé et traité avec succès.",
        "nom_fichier": nom,
        "nom_original": nom_original,
        "nombre_pages": len(pages),
        "nombre_segments": len(segments),
    }
