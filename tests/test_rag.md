## Test RAG avec Filtres

### TR01 [Général]
**Question :** Quelles sont les conditions pour obtenir une bourse ?
**Filtre :** Aucun (tous les documents)
**Réponse attendue :** Moyenne > 12/20, dossier complet, dépôt avant le 30 novembre, respect des conditions d'éligibilité et du dispositif demandé.
**Sources attendues :** 02_guide_bourses.txt
**Catégorie attendue dans les sources :** Guides pratiques

### TR02 [Filtré par catégorie]
**Question :** Quelles sont les sanctions en cas de fraude ?
**Filtre :** Catégorie = Règlements
**Réponse attendue :** Exclusion ou sanction disciplinaire, avec exclusion de 2 ans minimum dans certains cas.
**Sources attendues :** 01_reglement_interieur.txt ; 03_reglement_examens.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître.

### TR03 [Filtré par fichier]
**Question :** Quelles sont les étapes à suivre pour l'inscription ?
**Filtre :** Fichier = 05_procedure_inscription.txt
**Réponse attendue :** Dépôt du dossier, paiement des frais, validation administrative et inscription définitive.
**Vérification :** Seule la source 05_procedure_inscription.txt doit apparaître.

### TR04 [Hors corpus]
**Question :** Quel est le cours du Bitcoin aujourd'hui ?
**Filtre :** Aucun
**Réponse attendue :** "Je ne trouve pas cette information dans les documents."
**Vérification :** Le modèle ne doit pas inventer de réponse.

### TR05 [Malgache]
**Question :** Inona ny fepetra takiana hangataka bourse ?
**Filtre :** Aucun
**Réponse attendue :** Réponse en français ou indication qu'il ne comprend pas le malgache.
**Vérification :** Pas d'hallucination en malgache.

### TR06 [Général]
**Question :** Quelle est la date de la rentrée universitaire ?
**Filtre :** Aucun
**Réponse attendue :** La rentrée universitaire est fixée au 5 octobre 2026.
**Sources attendues :** 09_calendrier_universitaire.txt ; 04_guide_etudiant.txt
**Catégorie attendue dans les sources :** Organisation & plannings / Guides pratiques

### TR07 [Filtré par catégorie]
**Question :** Quels sont les droits et devoirs des étudiants ?
**Filtre :** Catégorie = Règlements
**Réponse attendue :** Suivre les enseignements, passer les examens, respecter les règles, faire preuve d'assiduité et d'honnêteté.
**Sources attendues :** 01_reglement_interieur.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître.

### TR08 [Filtré par fichier]
**Question :** Quelles sont les dates des examens ?
**Filtre :** Fichier = 09_calendrier_universitaire.txt
**Réponse attendue :** Session normale du semestre 1 : 12 au 30 janvier 2027 ; session de rattrapage : 7 au 18 juin 2027.
**Vérification :** Seule la source 09_calendrier_universitaire.txt doit apparaître.

### TR09 [Général]
**Question :** Quelles pièces sont nécessaires pour une demande de bourse ?
**Filtre :** Aucun
**Réponse attendue :** Carte d'étudiant, relevé de notes, attestation de revenus, acte de naissance, photos, attestation de non-cumul.
**Sources attendues :** 19_formulaire_bourse.txt ; 02_guide_bourses.txt
**Catégorie attendue dans les sources :** Formulaires & documents ponctuels / Guides pratiques

### TR10 [Filtré par catégorie]
**Question :** Quel est le calendrier des stages ?
**Filtre :** Catégorie = Guides pratiques
**Réponse attendue :** Le stage est obligatoire selon le cycle, avec des périodes conseillées et des durées spécifiques.
**Sources attendues :** 08_guide_stages.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître.

### TR11 [Général]
**Question :** Quelles sont les règles de la bibliothèque ?
**Filtre :** Aucun
**Réponse attendue :** Les horaires, le droit de prêt, les règles de conduite et les interdictions de certains documents.
**Sources attendues :** 06_reglement_bibliotheque.txt
**Catégorie attendue dans les sources :** Règlements

### TR12 [Filtré par fichier]
**Question :** Quelle est la procédure d'inscription ?
**Filtre :** Fichier = 05_procedure_inscription.txt
**Réponse attendue :** Conditions d'admission, dépôt du dossier, paiement des frais, validation administrative.
**Vérification :** Seule la source 05_procedure_inscription.txt doit apparaître.

### TR13 [Général]
**Question :** Quelles sont les sanctions disciplinaires possibles ?
**Filtre :** Aucun
**Réponse attendue :** Rappel à l'ordre, avertissement, blâme, interdiction temporaire, exclusion temporaire, exlcusion définitive.
**Sources attendues :** 07_procedure_disciplinaire.txt
**Catégorie attendue dans les sources :** Procédures

### TR14 [Filtré par catégorie]
**Question :** Où trouver le calendrier académique complet ?
**Filtre :** Catégorie = Organisation & plannings
**Réponse attendue :** Dans le calendrier académique officiel de l'année 2026-2027.
**Sources attendues :** 09_calendrier_universitaire.txt ; 10_organisation_pedagogique.txt
**Vérification :** Aucune source d'une autre catégorie ne doit apparaître.

### TR15 [Général]
**Question :** Quelles sont les pièces demandées pour le dossier d'inscription ?
**Filtre :** Aucun
**Réponse attendue :** Formulaire de candidature, diplôme du baccalauréat, acte de naissance, certificat médical, photos, carte d'identité, etc.
**Sources attendues :** 05_procedure_inscription.txt
**Catégorie attendue dans les sources :** Procédures

### TR16 [Hors sujet]
**Question :** Quelle est la meilleure stratégie pour investir en bourse ?
**Filtre :** Aucun
**Réponse attendue :** "Je ne trouve pas cette information dans les documents."
**Vérification :** Le modèle ne doit pas répondre hors corpus.

### TR17 [Malgache]
**Question :** Inona no manome ny daty amin'ny fanadinana ?
**Filtre :** Aucun
**Réponse attendue :** Réponse en français ou indication qu'il ne comprend pas le malgache.
**Vérification :** Pas d'hallucination en malgache.

### TR18 [Général]
**Question :** Que dit le guide sur les stages ?
**Filtre :** Aucun
**Réponse attendue :** Le stage est obligatoire selon le parcours, il faut signer une convention, rédiger un rapport et respecter les règles de l'organisme d'accueil.
**Sources attendues :** 08_guide_stages.txt ; 18_convention_stage.txt
**Catégorie attendue dans les sources :** Guides pratiques / Formulaires & documents ponctuels

### TR19 [Filtré par fichier]
**Question :** Quelles sont les règles d'emprunt à la bibliothèque ?
**Filtre :** Fichier = 06_reglement_bibliotheque.txt
**Réponse attendue :** Emprunt jusqu'à trois ouvrages, durée de 14 jours, renouvellement possible, retour au guichet ou boîte de dépôt.
**Vérification :** Seule la source 06_reglement_bibliotheque.txt doit apparaître.

### TR20 [Général]
**Question :** Quelles sont les dates clés de la campagne de bourses ?
**Filtre :** Aucun
**Réponse attendue :** Ouverture le 15 octobre 2026, clôture le 30 novembre 2026, publication le 20 décembre 2026, versements à partir de janvier 2027.
**Sources attendues :** 02_guide_bourses.txt ; 09_calendrier_universitaire.txt
**Catégorie attendue dans les sources :** Guides pratiques / Organisation & plannings
