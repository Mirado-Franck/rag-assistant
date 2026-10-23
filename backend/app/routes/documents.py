from fastapi import APIRouter, HTTPException

from app.stockage import obtenir_tous_les_documents, obtenir_document

router = APIRouter()


@router.get("/documents")
def lister_documents():
    """
    Retourne la liste de tous les documents uploadés.
    Ne renvoie pas les segments (trop volumineux), juste les métadonnées.
    """
    documents = obtenir_tous_les_documents()

    return {
        "nombre_documents": len(documents),
        "documents": documents
    }


@router.get("/documents/{nom_fichier}")
def detail_document(nom_fichier: str):
    """
    Retourne le détail d'un document, y compris ses segments.
    Utile pour le débogage et pour A1 qui aura besoin des segments
    pour construire l'index vectoriel.
    """
    document = obtenir_document(nom_fichier)

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{nom_fichier}' introuvable."
        )

    return document