import os
import json
from src.rag.classifier import classify_document

# --- CONFIG ---
PROCESSED_DIR = "data/processed"
# 5 fichiers représentatifs - un par catégorie
FILES_TO_TEST = [
    "01_reglement_interieur.txt",
    "05_procedure_inscription.txt",
    "08_guide_stages.txt",
    "09_calendrier_universitaire.txt",
    "19_formulaire_bourse.txt",
]

# Nom exact de ton modèle Ollama (vu avec ollama list)
MODEL_NAME = "llama3.2"

print("🧪 A1.3 — Test sur 5 vrais documents\n")
print(f"Modèle : {MODEL_NAME}\n")
print(f"Dossier : {PROCESSED_DIR}\n")

results = []

for filename in FILES_TO_TEST:
    filepath = os.path.join(PROCESSED_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️ Fichier introuvable : {filepath}")
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"📄 {filename} ({len(text)} caractères)")
    
    # Appel au classifieur
    try:
        result = classify_document(text, model_name=MODEL_NAME)
        print(f"   → Catégorie : {result['categorie']}")
        print(f"   → Confiance : {result['confiance']:.0%}")
        print(f"   → Justification : {result['justification']}\n")
        results.append((filename, result))
    except Exception as e:
        print(f"   ❌ Erreur : {e}\n")
        results.append((filename, {"categorie": "Erreur", "confiance": 0.0, "justification": str(e)}))

# --- Résumé ---
print("="*60)
print("📊 RÉSUMÉ A1.3")
print("="*60)

# Catégories attendues pour vérification
attendus = {
    "01_reglement_interieur.txt": "Règlements",
    "05_procedure_inscription.txt": "Procédures",
    "08_guide_stages.txt": "Guides pratiques",
    "09_calendrier_universitaire.txt": "Organisation & plannings",
    "19_formulaire_bourse.txt": "Formulaires & documents ponctuels",
}

correct = 0
for filename, r in results:
    attendu = attendus.get(filename, "?")
    ok = "✅" if r['categorie'] == attendu else "❌"
    if r['categorie'] == attendu:
        correct += 1
    confiance_icon = "✅" if r['confiance'] >= 0.8 else "⚠️"
    print(f"{ok} {filename}")
    print(f"   Prédit: {r['categorie']} ({r['confiance']:.0%}) {confiance_icon} | Attendu: {attendu}")
    print(f"   → {r['justification']}\n")

print(f"Score A1.3 : {correct}/5 = {correct/5:.0%}")

if correct == 5:
    print("🎉 Parfait ! A1.3 validé à 100%")
elif correct >= 3:
    print("👍 Bon baseline (60%+). Documente les cas limites pour le rapport Jour 7.")
else:
    print("⚠️ Score faible - vérifie ton prompt et les fichiers")

# Sauvegarder les résultats pour le rapport et pour B2
output = {k: v for k, v in results}
with open("tests_A1_3_resultats.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("\n💾 Résultats sauvegardés dans tests_A1_3_resultats.json")

# Test supplémentaire A1.4 : alternatives sur un cas ambigu
print("\n" + "="*60)
print("🧪 BONUS A1.4 — Test alternatives sur texte ambigu")
print("="*60)
from src.rag.classifier import classify_with_alternatives
texte_ambigu = "Le formulaire de demande de bourse doit être déposé conformément au règlement intérieur de l'université, selon la procédure suivante : étape 1, remplir le formulaire..."
result_alt = classify_with_alternatives(texte_ambigu, model_name=MODEL_NAME)
print(f"Principal : {result_alt['primary']['categorie']} ({result_alt['primary']['confiance']:.0%})")
print(f"Confirmation nécessaire : {result_alt['needs_confirmation']}")
if result_alt['alternatives']:
    print("Alternatives :")
    for alt in result_alt['alternatives']:
        print(f"  - {alt['categorie']} : {alt['probabilite']:.0%}")
else:
    print("(pas d'alternatives - confiance haute)")
