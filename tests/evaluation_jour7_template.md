# Évaluation Jour 7 — gabarit de résultats (A2)

> Gabarit vide à remplir avec les mesures réelles. Ne pas inscrire de résultats supposés. Les 20 items de classification doivent être les documents validés par l’équipe; le corpus indexé de la branche est actuellement de 16 sources / 200 chunks, donc préciser le périmètre exact avant de comparer les scores.

## A. Classification — 20 documents

Exécuter le classifieur sur chaque document avec le même protocole. Utiliser les catégories exactes de l’API. Calculer la précision brute `nombre correct / nombre testé`; noter les erreurs et les cas ambigus.

| ID | Fichier | Catégorie attendue | Prédiction | Confiance (%) | Correct (oui/non) | Temps (ms) | Notes / erreur |
|---|---|---|---|---:|---|---:|---|
| DOC01 |  |  |  |  |  |  |  |
| DOC02 |  |  |  |  |  |  |  |
| DOC03 |  |  |  |  |  |  |  |
| DOC04 |  |  |  |  |  |  |  |
| DOC05 |  |  |  |  |  |  |  |
| DOC06 |  |  |  |  |  |  |  |
| DOC07 |  |  |  |  |  |  |  |
| DOC08 |  |  |  |  |  |  |  |
| DOC09 |  |  |  |  |  |  |  |
| DOC10 |  |  |  |  |  |  |  |
| DOC11 |  |  |  |  |  |  |  |
| DOC12 |  |  |  |  |  |  |  |
| DOC13 |  |  |  |  |  |  |  |
| DOC14 |  |  |  |  |  |  |  |
| DOC15 |  |  |  |  |  |  |  |
| DOC16 |  |  |  |  |  |  |  |
| DOC17 |  |  |  |  |  |  |  |
| DOC18 |  |  |  |  |  |  |  |
| DOC19 |  |  |  |  |  |  |  |
| DOC20 |  |  |  |  |  |  |  |

**Synthèse classification :** corrects : ___ / 20 · précision brute : ___ % · temps moyen : ___ ms · médiane : ___ ms · principaux cas d’erreur : ___.

## B. RAG — 30 questions

Couvrir les questions générales, les filtres par catégorie, les filtres par fichier, les questions hors corpus et les questions en malgache. Pour une réponse évaluée, vérifier le contenu **et** que les sources citées étayent effectivement la réponse. Les réponses et durées doivent être observées, pas préremplies.

| ID | Type / filtre | Question | Source(s) attendue(s) | Réponse observée / adéquate ? | Source(s) observée(s) / correcte(s) ? | Temps (ms) | Hallucination / notes |
|---|---|---|---|---|---|---:|---|
| RAG01 |  |  |  |  |  |  |  |
| RAG02 |  |  |  |  |  |  |  |
| RAG03 |  |  |  |  |  |  |  |
| RAG04 |  |  |  |  |  |  |  |
| RAG05 |  |  |  |  |  |  |  |
| RAG06 |  |  |  |  |  |  |  |
| RAG07 |  |  |  |  |  |  |  |
| RAG08 |  |  |  |  |  |  |  |
| RAG09 |  |  |  |  |  |  |  |
| RAG10 |  |  |  |  |  |  |  |
| RAG11 |  |  |  |  |  |  |  |
| RAG12 |  |  |  |  |  |  |  |
| RAG13 |  |  |  |  |  |  |  |
| RAG14 |  |  |  |  |  |  |  |
| RAG15 |  |  |  |  |  |  |  |
| RAG16 |  |  |  |  |  |  |  |
| RAG17 |  |  |  |  |  |  |  |
| RAG18 |  |  |  |  |  |  |  |
| RAG19 |  |  |  |  |  |  |  |
| RAG20 |  |  |  |  |  |  |  |
| RAG21 |  |  |  |  |  |  |  |
| RAG22 |  |  |  |  |  |  |  |
| RAG23 |  |  |  |  |  |  |  |
| RAG24 |  |  |  |  |  |  |  |
| RAG25 |  |  |  |  |  |  |  |
| RAG26 |  |  |  |  |  |  |  |
| RAG27 |  |  |  |  |  |  |  |
| RAG28 |  |  |  |  |  |  |  |
| RAG29 |  |  |  |  |  |  |  |
| RAG30 |  |  |  |  |  |  |  |

**Synthèse RAG :** réponses adéquates : ___ / 30 · source attendue retrouvée : ___ / ___ · refus correct hors corpus : ___ / ___ · hallucinations observées : ___ · temps moyen : ___ ms · p95 : ___ ms.

## Méthode et conditions à consigner

- Date/heure, machine, version du modèle Ollama, versions Python et dépendances.
- État du corpus et de ChromaDB (nombre de sources et de chunks au début du test).
- Pour chaque requête : question exacte, filtres exacts (`category`, `source_file`), réponse brute, sources retournées et `temps_ms`.
- Garder les échecs HTTP séparés des erreurs de pertinence; inscrire le code HTTP et le détail.
- Mesurer la latence sur une machine locale à titre indicatif; ne pas comparer des durées prises sur des matériels différents comme si les conditions étaient identiques.
