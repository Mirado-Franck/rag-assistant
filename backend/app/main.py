from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.documents import router as documents_router

# Créer l'application FastAPI
app = FastAPI(
    title="MadaDoc AI - API",
    description="API backend pour l'assistant documentaire universitaire",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routes
app.include_router(upload_router)
app.include_router(documents_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "MadaDoc AI - API fonctionnelle"
    }


@app.get("/")
def racine():
    return {
        "application": "MadaDoc AI",
        "version": "0.1.0",
        "documentation": "/docs"
    }