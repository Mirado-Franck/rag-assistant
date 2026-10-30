"""JOUR 6 A1.4 - Mesure des temps de réponse (10 requêtes)"""
import time
import requests
import json

API_URL = "http://localhost:8000"

questions = [
    "Quelles sont les conditions pour obtenir une bourse ?",
    "Quelles sont les sanctions en cas de fraude ?",
    "Comment s'inscrire à l'université ?",
    "Quelles sont les dates de la rentrée ?",
    "Inona ny fepetra takiana hangataka bourse ?",
    "Quel est le cours du Bitcoin ?",
    "Comment obtenir une convention de stage ?",
    "Quels sont les horaires de la bibliothèque ?",
    "Quelles pièces fournir pour l'inscription ?",
    "Quelle est la procédure disciplinaire ?"
]

print("="*60)
print("📊 JOUR 6 A1.4 - MESURE DES TEMPS DE RÉPONSE")
print("="*60)

# Test classification via upload (simulé avec texte)
print("\n1. Test HEALTH")
start = time.time()
r = requests.get(f"{API_URL}/api/health")
print(f"   Health: {r.status_code} - {r.json()['status']} - {time.time()-start:.3f}s")

# Test RAG
print("\n2. Test RAG (10 questions)")
temps_list = []
for i, q in enumerate(questions, 1):
    start = time.time()
    try:
        r = requests.post(f"{API_URL}/api/query", json={"question": q, "n_results": 4})
        data = r.json()
        elapsed = data.get("temps_ms", (time.time()-start)*1000)
        temps_list.append(elapsed)
        status = "✅" if elapsed < 15000 else "⚠️ lent"
        print(f"   {status} Q{i}: {elapsed:.0f}ms - {q[:40]}...")
    except Exception as e:
        print(f"   ❌ Q{i} erreur: {e}")

if temps_list:
    print(f"\n📈 Moyenne: {sum(temps_list)/len(temps_list):.0f}ms")
    print(f"   Min: {min(temps_list):.0f}ms | Max: {max(temps_list):.0f}ms")
    print(f"   <5s: {sum(1 for t in temps_list if t < 5000)}/10")
    print(f"   <15s: {sum(1 for t in temps_list if t < 15000)}/10")

print("\n✅ Mesures terminées - à mettre dans rapport section 6")
