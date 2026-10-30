# Rapport — Assistant RAG avec classification de documents

## 1. Introduction
- Contexte et objectifs : classification documentaire et réponses RAG locales.
- Enjeu de souveraineté des données et périmètre de l'évaluation.

## 2. Architecture technique
- Schéma global (à insérer).
- Stack : Ollama, LangChain, Sentence Transformers, ChromaDB, FastAPI et Streamlit.
- Cinq catégories documentaires et workflow : Upload → Classification → Confirmation → Indexation → Recherche/RAG.

## 3. Corpus de données
- Liste et répartition des sources par catégorie (à finaliser après synchronisation des documents B2).
- Traçabilité de l'extraction, du découpage et de l'indexation.
- À l'état initial de cette branche : 16 sources et 200 chunks. Distinguer ce corpus indexé des 20 documents éventuellement évalués pour la classification.

## 4. Module de classification
- Méthode et prompt du classifieur réel (A1).
- Résultats des 20 documents, erreurs et cas ambigus : à compléter après mesure B2.

## 5. Module RAG
- Recherche vectorielle, génération locale, filtres catégorie/fichier et format de citation des sources.
- Analyse qualitative et limites de la réponse : à compléter après les 30 essais.

## 6. Architecture finale et déploiement
- Architecture finale, gestion des erreurs, journaux, démarrage local et versions utilisées (A1).
- Conditions de reproductibilité : même corpus, mêmes modèles et même machine pour les comparaisons de latence.

## 7. Évaluation

Les valeurs ci-dessous sont **à mesurer**; aucune mesure n'est préremplie. Le détail des lignes à renseigner est dans [`tests/evaluation_jour7_template.md`](../tests/evaluation_jour7_template.md). Les sorties brutes du script de stress sont enregistrées localement dans `tests/results/` (dossier ignoré par Git).

### 7.1 Classification — 20 documents

| Mesure | Résultat |
|---|---:|
| Documents testés | ___ / 20 |
| Catégories prédites correctement | ___ / 20 |
| Précision brute | ___ % |
| Temps moyen / médian | ___ / ___ ms |
| Erreurs principales | À compléter |

Précision brute : `nombre de catégories correctes / nombre de documents effectivement évalués × 100`. Signaler séparément les documents illisibles ou non évalués; ne pas les compter comme succès.

### 7.2 RAG — 30 questions

| Mesure | Résultat |
|---|---:|
| Questions avec réponse HTTP 200 | ___ / 30 |
| Réponses jugées adéquates par l'évaluateur | ___ / 30 |
| Source attendue retrouvée (parmi les cas avec source attendue) | ___ / ___ |
| Refus correct sur questions hors corpus | ___ / ___ |
| Hallucinations ou citations non étayées | ___ |
| Temps RAG moyen / médian / p95 | ___ / ___ / ___ ms |

Une réponse HTTP 200 ne signifie pas automatiquement que la réponse est correcte. Vérifier séparément la pertinence, l'appui sur les extraits cités et l'absence d'affirmations non présentes dans le corpus. Pour les questions en malgache, consigner explicitement la langue et la qualité de la réponse.

### 7.3 Robustesse et performances

| Indicateur | Résultat / observation |
|---|---|
| Corpus testé (sources / chunks) | ___ / ___ |
| Requêtes RAG exécutées / erreurs HTTP | ___ / ___ |
| Machine et modèle Ollama | À renseigner |
| Temps moyen et p95 mesurés sur la même machine | ___ / ___ ms |
| Cas limites API (upload corrompu, question vide, catégorie inconnue) | À renseigner |

## 8. Limites et biais
- Limites techniques : données d'extraction, taille de contexte, latence locale, dépendance aux modèles installés.
- Biais et réponses non étayées observés pendant les évaluations : à documenter sans les masquer.
- Limites linguistiques, notamment pour le malgache : à compléter après les tests.

## 9. Étude de coût
- Configuration locale actuelle et matériel utilisé.
- Configuration recommandée.
- Comparaison qualitative local / cloud et contraintes de confidentialité.

## 10. Conclusion
- Bilan des résultats, limites restantes et améliorations prioritaires (à compléter après l'évaluation).
