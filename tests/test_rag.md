## Test RAG avec Filtres

### TR01 [Général]
**Question :** Quelles sont les conditions pour obtenir une bourse ?
**Filtre :** Aucun (tous les documents)
**Réponse attendue :** Moyenne > 12/20, dossier complet, dépôt avant le 30/10
**Sources attendues :** 02_guide_bourses.txt
**Catégorie attendue dans les sources :** Guides pratiques

### TR02 [Filtré par catégorie]
**Question :** Quelles sont les sanctions en cas de fraude ?
**Filtre :** Catégorie = Règlements
**Réponse attendue :** Exclusion de 2 ans minimum
**Sources attendues :** 01_reglement_interieur.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître

### TR03 [Filtré par fichier]
**Question :** Quelles sont les étapes à suivre ?
**Filtre :** Fichier = 03_procedure_inscription.txt
**Réponse attendue :** Les étapes spécifiques de l'inscription
**Vérification :** Seule la source 03_procedure_inscription.txt doit apparaître

### TR04 [Hors corpus]
**Question :** Quel est le cours du Bitcoin aujourd'hui ?
**Filtre :** Aucun
**Réponse attendue :** "Je ne trouve pas cette information dans les documents"
**Vérification :** Le modèle ne doit PAS inventer de réponse

### TR05 [Malgache]
**Question :** Inona ny fepetra takiana hangataka bourse ?
**Filtre :** Aucun
**Réponse attendue :** Réponse en français ou indication qu'il ne comprend pas le malgache
**Vérification :** Pas d'hallucination en malgache

### TR06 [Général]
**Question :** Quelle est la date de la rentrée universitaire ?
**Filtre :** Aucun
**Réponse attendue :** 5 octobre 2026
**Sources attendues :** 09_calendrier_universitaire.txt
**Catégorie attendue dans les sources :** Organisation & plannings

### TR07 [Filtré par catégorie]
**Question :** Quels sont les droits et devoirs des étudiants ?
**Filtre :** Catégorie = Règlements
**Réponse attendue :** Les droits et devoirs de base de l'étudiant
**Sources attendues :** 01_reglement_interieur.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître

### TR08 [Filtré par fichier]
**Question :** Quelles sont les dates des examens ?
**Filtre :** Fichier = 09_calendrier_universitaire.txt
**Réponse attendue :** Les dates de la session normale et de rattrapage
**Vérification :** Seule la source 09_calendrier_universitaire.txt doit apparaître

### TR09 [Général]
**Question :** Quelles pièces sont nécessaires pour une demande de bourse ?
**Filtre :** Aucun
**Réponse attendue :** Carte d'étudiant, relevé de notes, attestation de revenus, acte de naissance
**Sources attendues :** 19_formulaire_bourse.txt
**Catégorie attendue dans les sources :** Formulaires & documents ponctuels

### TR10 [Filtré par catégorie]
**Question :** Quel est le calendrier des stages ?
**Filtre :** Catégorie = Guides pratiques
**Réponse attendue :** Périodes recommandées et modalités du stage
**Sources attendues :** 08_guide_stages.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître

### TR11 [Général]
**Question :** Quelles sont les règles de la bibliothèque ?
**Filtre :** Aucun
**Réponse attendue :** Horaires, emprunts, accès et conduite
**Sources attendues :** 06_reglement_bibliotheque.txt
**Catégorie attendue dans les sources :** Règlements

### TR12 [Filtré par fichier]
**Question :** Quelle est la procédure d'inscription ?
**Filtre :** Fichier = 05_procedure_inscription.txt
**Réponse attendue :** Les étapes et pièces de l'inscription
**Vérification :** Seule la source 05_procedure_inscription.txt doit apparaître

### TR13 [Général]
**Question :** Quels sont les cas de sanction disciplinaire ?
**Filtre :** Aucun
**Réponse attendue :** Fautes mineures, graves et très graves
**Sources attendues :** 07_procedure_disciplinaire.txt
**Catégorie attendue dans les sources :** Procédures

### TR14 [Filtré par catégorie]
**Question :** Où trouver le calendrier académique complet ?
**Filtre :** Catégorie = Organisation & plannings
**Réponse attendue :** Dans le calendrier universitaire
**Sources attendues :** 09_calendrier_universitaire.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître

### TR15 [Général]
**Question :** Quelles sont les pièces demandées pour le dossier d'inscription ?
**Filtre :** Aucun
**Réponse attendue :** Formulaire, diplôme, acte de naissance, certificat médical, photos, etc.
**Sources attendues :** 05_procedure_inscription.txt
**Catégorie attendue dans les sources :** Procédures

### TR16 [Hors sujet]
**Question :** Quelle est la meilleure stratégie pour investir en bourse ?
**Filtre :** Aucun
**Réponse attendue :** "Je ne trouve pas cette information dans les documents"
**Vérification :** Le modèle ne doit pas répondre hors corpus

### TR17 [Malgache]
**Question :** Inona no manome ny daty amin'ny fanadinana ?
**Filtre :** Aucun
**Réponse attendue :** Réponse en français ou indication qu'il ne comprend pas le malgache
**Vérification :** Pas d'hallucination en malgache

### TR18 [Général]
**Question :** Que dit le guide sur les stages ?
**Filtre :** Aucun
**Réponse attendue :** Les conditions, la convention et le rapport de stage
**Sources attendues :** 08_guide_stages.txt
**Catégorie attendue dans les sources :** Guides pratiques

### TR19 [Filtré par fichier]
**Question :** Quelles sont les règles d'emprunt à la bibliothèque ?
**Filtre :** Fichier = 06_reglement_bibliotheque.txt
**Réponse attendue :** Règles de prêt et de restitution
**Vérification :** Seule la source 06_reglement_bibliotheque.txt doit apparaître

### TR20 [Général]
**Question :** Quelles sont les dates clés de la campagne de bourses ?
**Filtre :** Aucun
**Réponse attendue :** Ouverture 15 octobre, clôture 30 novembre, publication 20 décembre
**Sources attendues :** 02_guide_bourses.txt
**Catégorie attendue dans les sources :** Guides pratiques
