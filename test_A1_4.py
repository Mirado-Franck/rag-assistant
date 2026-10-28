from src.rag.classifier import classify_document, classify_with_alternatives
import pathlib

MODEL_NAME = "llama3.2"

print("="*60)
print("🧪 A1.4 — Tester la fonction d'alternatives")
print("="*60)
print(f"Modèle : {MODEL_NAME}\n")

# Test 1 : Texte AMBIGU (mélange formulaire + règlement + procédure)
# C'est le cas le plus important : doit déclencher une confirmation
texte_ambigu = (
    "Le formulaire de demande de bourse doit être déposé "
    "conformément au règlement intérieur de l'université, selon la procédure "
    "suivante : étape 1, remplir le formulaire, étape 2, joindre les pièces, "
    "étape 3, déposer au bureau des bourses avant le 30 novembre."
)

print("📄 TEST 1 : Texte AMBIGU (formulaire + règlement + procédure)")
print(f"Texte : {texte_ambigu[:100]}...\n")
result = classify_with_alternatives(texte_ambigu, model_name=MODEL_NAME)
print(f"→ Principal : {result['primary']['categorie']} ({result['primary']['confiance']:.0%})")
print(f"→ Justification : {result['primary']['justification']}")
print(f"→ Confirmation nécessaire : {result['needs_confirmation']}")
if result['alternatives']:
    print("→ Alternatives proposées :")
    for alt in result['alternatives']:
        print(f"     - {alt['categorie']} : {alt['probabilite']:.0%}")
else:
    print("→ Alternatives : aucune (confiance haute)")
print()

# Test 2 : Texte CLAIR (règlement pur) -> doit PAS demander de confirmation
texte_clair = pathlib.Path("data/processed/01_reglement_interieur.txt").read_text(encoding="utf-8") if pathlib.Path("data/processed/01_reglement_interieur.txt").exists() else "Article 12 : Tout étudiant doit s'acquitter des frais avant le 30 septembre. Article 13 : L'exclusion définitive sera prononcée en cas de fraude."

print("📄 TEST 2 : Texte CLAIR (01_reglement_interieur.txt)")
print(f"Texte : {texte_clair[:100]}...\n")
result2 = classify_with_alternatives(texte_clair, model_name=MODEL_NAME)
print(f"→ Principal : {result2['primary']['categorie']} ({result2['primary']['confiance']:.0%})")
print(f"→ Justification : {result2['primary']['justification']}")
print(f"→ Confirmation nécessaire : {result2['needs_confirmation']}")
if result2['alternatives']:
    print("→ Alternatives :")
    for alt in result2['alternatives']:
        print(f"     - {alt['categorie']} : {alt['probabilite']:.0%}")
else:
    print("→ Alternatives : aucune (normal, confiance haute)")
print()

# Test 3 : Autre cas limite réel - calendrier (maintenant corrigé mais on vérifie qu'il ne déclenche pas confirmation)
try:
    texte_calendrier = pathlib.Path("data/processed/09_calendrier_universitaire.txt").read_text(encoding="utf-8")
    print("📄 TEST 3 : Cas réel 09_calendrier_universitaire.txt (doit être clair maintenant)")
    print(f"Texte : {texte_calendrier[:100]}...\n")
    result3 = classify_with_alternatives(texte_calendrier, model_name=MODEL_NAME)
    print(f"→ Principal : {result3['primary']['categorie']} ({result3['primary']['confiance']:.0%})")
    print(f"→ Confirmation nécessaire : {result3['needs_confirmation']}")
    if result3['alternatives']:
        print("→ Alternatives :")
        for alt in result3['alternatives']:
            print(f"     - {alt['categorie']} : {alt['probabilite']:.0%}")
    else:
        print("→ Alternatives : aucune")
    print()
except FileNotFoundError:
    print("⚠️ 09_calendrier_universitaire.txt introuvable, test 3 ignoré\n")

# --- Résumé validation ---
print("="*60)
print("✅ CHECKLIST A1.4")
print("="*60)
check1 = result['needs_confirmation'] == True and len(result['alternatives']) > 0
check2 = result2['needs_confirmation'] == False and len(result2['alternatives']) == 0

print(f"{'✅' if check1 else '❌'} Test ambigu -> needs_confirmation=True + alternatives présentes")
print(f"   Actuel : needs_confirmation={result['needs_confirmation']}, {len(result['alternatives'])} alternatives")
print()
print(f"{'✅' if check2 else '❌'} Test clair -> needs_confirmation=False + pas d'alternatives")
print(f"   Actuel : needs_confirmation={result2['needs_confirmation']}, {len(result2['alternatives'])} alternatives")
print()

if check1 and check2:
    print("🎉 A1.4 VALIDÉ ! La fonction d'alternatives marche parfaitement.")
    print("Demain (Jour 4), B1 pourra afficher les boutons de confirmation dans l'UI.")
else:
    print("⚠️ Ajustement nécessaire :")
    if not check1:
        print("  - Le texte ambigu devrait déclencher needs_confirmation=True (confiance <0.8)")
        print("  - Ton LLM est trop confiant (donne 0.95 même sur ambigu). C'est le biais de sur-confiance.")
        print("  - Solution Jour 4 : on baissera le seuil à 0.85 ou on forcera la confirmation pour les cas mixtes.")
    if not check2:
        print("  - Le texte clair ne devrait PAS demander de confirmation")
print()
print("Commit à faire :")
print('git add src/rag/classifier.py test_A1_4.py && git commit -m "Jour 3 A1.4 : fonction alternatives validée"')
