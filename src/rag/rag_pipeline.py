import chromadb
from chromadb.config import Settings
from langchain_ollama import ChatOllama
from sentence_transformers import SentenceTransformer
import time
import os

# Configuration
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama3.2"

# Prompt RAG (le cœur de la qualité des réponses)
RAG_PROMPT = """Tu es un assistant documentaire spécialisé dans les documents 
institutionnels. Ta mission est de répondre aux questions des utilisateurs en te 
basant UNIQUEMENT sur les extraits de documents fournis ci-dessous.

RÈGLES STRICTES :
1. Réponds UNIQUEMENT en utilisant les informations du CONTEXTE.
2. Si la réponse ne se trouve PAS dans le contexte, dis exactement :
   "Je ne trouve pas cette information dans les documents disponibles."
3. Ne JAMAIS inventer d'information, de chiffre, de date ou de nom.
4. Cite la source (nom du fichier) quand tu utilises une information.
5. Si le contexte contient des informations contradictoires, signale-le.
6. Réponds en français, de manière claire et structurée.

CONTEXTE (extraits de documents) :
---
{context}
---

QUESTION DE L'UTILISATEUR : {question}

RÉPONSE :"""


class RAGPipeline:
    """Pipeline RAG complet avec filtres par catégorie et par fichier."""
    
    def __init__(self):
        """Initialise le pipeline (modèles + base de données)."""
        print("🔄 Initialisation du pipeline RAG...")
        
        # 1. Connexion à ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
        print(f"  ✅ ChromaDB connecté ({self.collection.count()} chunks)")
        
        # 2. Modèle d'embedding
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        print(f"  ✅ Embedding model chargé")
        
        # 3. LLM local
        self.llm = ChatOllama(
            model=LLM_MODEL,
            temperature=0.1,
            num_predict=512
        )
        print(f"  ✅ LLM chargé ({LLM_MODEL})")
        print("🚀 Pipeline RAG prêt !\n")
    
    def search(self, question, n_results=4, category=None, source_file=None):
        """
        Recherche sémantique dans ChromaDB avec filtres optionnels.
        
        Args:
            question: La question de l'utilisateur
            n_results: Nombre de chunks à récupérer
            category: Filtre par catégorie (ex: "Règlements")
            source_file: Filtre par fichier (ex: "01_reglement.txt")
        
        Returns:
            list of dict: Les chunks trouvés avec métadonnées
        """
        # Construire le filtre ChromaDB
        where_filter = None
        if category and source_file:
            where_filter = {
                "$and": [
                    {"categorie": category},
                    {"source": source_file}
                ]
            }
        elif category:
            where_filter = {"categorie": category}
        elif source_file:
            where_filter = {"source": source_file}
        
        # Calculer l'embedding de la question
        query_embedding = self.embedder.encode(question).tolist()
        
        # Requête ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"  ⚠️ Erreur de recherche : {e}")
            return []
        
        # Formater les résultats
        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "text": doc,
                    "source": results["metadatas"][0][i].get("source", "inconnu"),
                    "categorie": results["metadatas"][0][i].get("categorie", "inconnu"),
                    "distance": results["distances"][0][i] if results["distances"] else None,
                    "chunk_index": results["metadatas"][0][i].get("chunk_index", 0)
                })
        
        return chunks
    
    def generate_response(self, question, chunks):
        """
        Génère une réponse à partir des chunks trouvés.
        
        Args:
            question: La question de l'utilisateur
            chunks: Les chunks trouvés par la recherche
        
        Returns:
            str: La réponse générée par le LLM
        """
        if not chunks:
            return "Je ne trouve pas cette information dans les documents disponibles."
        
        # Construire le contexte à partir des chunks
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"[Source : {chunk['source']} | Catégorie : {chunk['categorie']}]\n"
                f"{chunk['text']}"
            )
        context = "\n\n---\n\n".join(context_parts)
        
        # Construire le prompt complet
        prompt = RAG_PROMPT.format(
            context=context,
            question=question
        )
        
        # Appeler le LLM
        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def query(self, question, n_results=4, category=None, source_file=None):
        """
        Méthode principale : recherche + génération en une seule étape.
        
        Args:
            question: La question de l'utilisateur
            n_results: Nombre de sources à utiliser
            category: Filtre par catégorie (optionnel)
            source_file: Filtre par fichier (optionnel)
        
        Returns:
            dict: {
                "question": str,
                "reponse": str,
                "sources": list,
                "filtre": str,
                "temps_ms": float,
                "nb_chunks_trouves": int
            }
        """
        start_time = time.time()
        
        # 1. Recherche
        chunks = self.search(
            question=question,
            n_results=n_results,
            category=category,
            source_file=source_file
        )
        
        # 2. Génération
        reponse = self.generate_response(question, chunks)
        
        # 3. Formater les sources (dédoublonnées)
        sources = []
        seen = set()
        for chunk in chunks:
            key = f"{chunk['source']}_{chunk['chunk_index']}"
            if key not in seen:
                sources.append({
                    "fichier": chunk["source"],
                    "categorie": chunk["categorie"],
                    "extrait": chunk["text"][:150] + "..."
                })
                seen.add(key)
        
        elapsed = (time.time() - start_time) * 1000
        
        # Décrire le filtre actif
        if category and source_file:
            filtre = f"catégorie={category} + fichier={source_file}"
        elif category:
            filtre = f"catégorie={category}"
        elif source_file:
            filtre = f"fichier={source_file}"
        else:
            filtre = "aucun (tous les documents)"
        
        return {
            "question": question,
            "reponse": reponse,
            "sources": sources,
            "filtre": filtre,
            "temps_ms": round(elapsed, 1),
            "nb_chunks_trouves": len(chunks)
        }


# === TESTS ===
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTS DU PIPELINE RAG")
    print("=" * 60)
    
    rag = RAGPipeline()
    
    # Test 1 : Question générale (sans filtre)
    print("\n" + "=" * 60)
    print("TEST 1 : Question générale (sans filtre)")
    print("=" * 60)
    result = rag.query("Quelles sont les conditions pour obtenir une bourse ?")
    print(f"❓ Question : {result['question']}")
    print(f"🔍 Filtre : {result['filtre']}")
    print(f"📝 Réponse :\n{result['reponse']}")
    print(f"\n📎 Sources ({len(result['sources'])}) :")
    for s in result['sources']:
        print(f"  • [{s['categorie']}] {s['fichier']}")
    print(f"⏱️ Temps : {result['temps_ms']} ms")
    
    # Test 2 : Question avec filtre par catégorie
    print("\n" + "=" * 60)
    print("TEST 2 : Question filtrée par catégorie (Règlements)")
    print("=" * 60)
    result = rag.query(
        "Quelles sont les sanctions en cas de fraude ?",
        category="Règlements"
    )
    print(f"❓ Question : {result['question']}")
    print(f"🔍 Filtre : {result['filtre']}")
    print(f"📝 Réponse :\n{result['reponse']}")
    print(f"\n📎 Sources ({len(result['sources'])}) :")
    for s in result['sources']:
        print(f"  • [{s['categorie']}] {s['fichier']}")
        # Vérifier que toutes les sources sont bien "Règlements"
        assert s['categorie'] == 'Règlements', \
            f"❌ ERREUR : source {s['fichier']} n'est pas dans Règlements !"
    print("  ✅ Toutes les sources sont bien de la catégorie 'Règlements'")
    
    # Test 3 : Question avec filtre par fichier
    print("\n" + "=" * 60)
    print("TEST 3 : Question filtrée par fichier")
    print("=" * 60)
    # Adapte le nom du fichier à ton corpus réel
    result = rag.query(
        "Quelles sont les étapes à suivre ?",
        source_file="03_procedure_inscription.txt"
    )
    print(f"❓ Question : {result['question']}")
    print(f"🔍 Filtre : {result['filtre']}")
    print(f"📝 Réponse :\n{result['reponse']}")
    print(f"\n📎 Sources ({len(result['sources'])}) :")
    for s in result['sources']:
        print(f"  • [{s['categorie']}] {s['fichier']}")
    
    # Test 4 : Question hors corpus (doit dire "je ne sais pas")
    print("\n" + "=" * 60)
    print("TEST 4 : Question hors corpus (test d'hallucination)")
    print("=" * 60)
    result = rag.query("Quel est le cours du Bitcoin aujourd'hui ?")
    print(f"❓ Question : {result['question']}")
    print(f"📝 Réponse :\n{result['reponse']}")
    if "ne trouve pas" in result['reponse'].lower() or \
       "pas d'information" in result['reponse'].lower():
        print("  ✅ Le modèle a correctement refusé de répondre")
    else:
        print("  ⚠️ ATTENTION : le modèle a peut-être halluciné !")
    
    # Test 5 : Question en malgache
    print("\n" + "=" * 60)
    print("TEST 5 : Question en malgache")
    print("=" * 60)
    result = rag.query("Inona ny fepetra takiana hangataka bourse ?")
    print(f"❓ Question : {result['question']}")
    print(f"📝 Réponse :\n{result['reponse']}")
    
    print("\n" + "=" * 60)
    print("🏁 TESTS TERMINÉS")
    print("=" * 60)