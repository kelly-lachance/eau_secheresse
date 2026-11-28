# Projet portfolio : pipeline de suivi de la sécheresse (Hub'Eau)

## L'idée en une phrase
Un pipeline ELT qui collecte chaque jour le niveau des nappes phréatiques d'Île-de-France (API Hub'Eau ; V1 démarrée sur les Yvelines, élargie aux 8 départements franciliens en semaine 2). Il historise ces mesures, les croise avec la météo (Open-Meteo) et calcule des indicateurs de sécheresse visibles dans un petit dashboard.

## Architecture visée (V1)
```
API Hub'Eau (nappes)  ─┐
                       ├─> Python (extract + load) ─> base locale (SQLite puis DuckDB)
API Open-Meteo (pluie) ─┘        │                              │
                                 │                     dbt : staging -> marts + tests
                     orchestrateur (Prefect) lance tout chaque jour      │
                                                              dashboard (Streamlit)
```
Tout tourne en local et le code vit sur GitHub. C'est ce dépôt GitHub qui ira dans ton portfolio.

## Rythme
**Préférence de Kelly :** 2 questions essentielles maximum par message. On privilégie l'avancement du projet, et les questions de compréhension servent seulement quand elles débloquent quelque chose.

Le planning compte 5 semaines. Chaque semaine prévoit 4 petites séances en semaine (15-30 min) et 2 séances de 2h le week-end. En semaine, on fait de la lecture, des exos courts et des petites corrections. Le week-end, on construit les gros morceaux. Si une notion bloque, on fait une pause exo dessus : on ne passe à l'étape suivante que quand tu sais **expliquer** ce que fait ton code.

---

## Semaine 1 : découvrir l'API et faire un premier chargement brut
**Objectif :** récupérer les mesures d'une station et les stocker telles quelles dans SQLite.

- Semaine : installer l'environnement (Python, environnement virtuel, Git, un dépôt GitHub vide avec un README). Explorer la documentation Hub'Eau « Piézométrie » dans le navigateur. Choisir ton département et 5 à 10 stations.
- Week-end 1 : écrire un script `extract.py` qui appelle l'API pour **une** station et sauvegarde la réponse JSON brute.
- Week-end 2 : écrire `load.py` qui insère ces mesures dans une table `raw_mesures_nappes` de SQLite (ce qu'on a déjà vu ensemble : connexion, curseur, requêtes paramétrées, commit).

**Notions :** requête HTTP (GET, paramètres, codes de retour), format JSON, pagination d'une API, différence entre donnée brute et donnée transformée (le « EL » de ELT).
**Livrable :** une table SQLite remplie et un premier commit sur GitHub.
**Tu sais expliquer :** pourquoi on stocke d'abord le brut sans le transformer.

## Semaine 2 : rendre l'ingestion fiable et incrémentale
**Objectif :** pouvoir relancer le script chaque jour sans doublons ni plantage.

- Semaine : élargir aux 8 départements d'Île-de-France (75, 77, 78, 91, 92, 93, 94, 95), le département étant un paramètre du code ; boucler sur toutes les stations, gérer la pagination et les erreurs (API indisponible, station sans données), ajouter des logs.
- Week-end 1 : passer au **chargement incrémental**. Le script cherche la dernière date déjà chargée et ne demande à l'API que ce qui est nouveau. Il rend aussi le chargement **idempotent** : le relancer deux fois donne le même résultat.
- Week-end 2 : migrer de SQLite vers **DuckDB**, une base orientée colonnes, plus adaptée à l'analytique, et comprendre pourquoi.

**Notions :** incrémental et full refresh, idempotence, clé unique, base orientée lignes et base orientée colonnes.
**Livrable :** un script qu'on peut lancer tous les jours sans risque.
**Tu sais expliquer :** ce qui se passe si le script plante au milieu et qu'on le relance.

## Semaine 3 : transformer avec dbt
**Objectif :** passer des données brutes à des tables propres et à des indicateurs.

- Semaine : installer dbt (avec l'adaptateur DuckDB), comprendre la structure d'un projet dbt, déclarer ta table brute comme `source`.
- Week-end 1 : créer les modèles de **staging** (renommage, typage, nettoyage) puis une dimension `dim_stations` et une table de faits `fct_niveaux_journaliers`.
- Week-end 2 : calculer un indicateur de sécheresse, par exemple l'écart du niveau du jour à la moyenne historique du même mois, avec des fonctions de fenêtrage. Ajouter des **tests dbt** (not_null, unique, relationships).

- **Snowflake (choix du 21/11) :** activer l'essai gratuit Snowflake au début de cette semaine (pas avant), charger le brut dans un stage puis `COPY INTO` une colonne `VARIANT`, et déclarer deux cibles dbt : DuckDB en local et Snowflake dans le cloud. Le projet doit rester utilisable en local après la fin de l'essai.

**Notions :** couches staging / marts, `ref()` et `source()`, entrepôt cloud (Snowflake, stage, VARIANT), star schema (faits et dimensions), fonctions de fenêtrage, tests de données.
**Livrable :** un `dbt build` qui passe, avec ses tests au vert.
**Tu sais expliquer :** la différence entre une table de faits et une dimension, avec ton propre projet comme exemple.

## Semaine 4 : ajouter la météo et orchestrer
**Objectif :** croiser deux sources et automatiser le pipeline.

- Semaine : explorer l'API Open-Meteo (précipitations et évapotranspiration journalières) et l'ingérer aux coordonnées de tes stations, avec le même modèle que les semaines 1 et 2.
- Week-end 1 : joindre météo et nappes dans dbt. Le défi : les granularités ne sont pas les mêmes (point GPS ou station, cumul ou mesure ponctuelle).
- Week-end 2 : orchestrer avec **Prefect**. Un flow enchaîne extraction Hub'Eau, extraction météo puis `dbt build`, et est planifié chaque jour.

- **Machine learning (choix du 24/11) :** en fin de semaine, environ 2 séances, regrouper les stations par comportement avec un **clustering (KMeans)** sur des variables calculées dans dbt (amplitude saisonnière, vitesse de réaction à la pluie, tendance). Le résultat, « nappes réactives » contre « nappes inertielles », sera affiché sur la carte Streamlit. Le ML reste un consommateur des tables propres du pipeline.

**Notions :** jointure de sources hétérogènes, DAG (graphe de dépendances entre tâches), planification, relance en cas d'échec.
**Livrable :** un pipeline complet déclenché automatiquement.
**Tu sais expliquer :** pourquoi un orchestrateur plutôt qu'un simple cron.

## Semaine 5 : rendre le projet présentable
**Objectif :** que quelqu'un comprenne ton projet en 2 minutes.

- Semaine : construire un petit dashboard **Streamlit** (carte des stations en alerte, courbe nappe et pluie pour une station).
- Week-end 1 : écrire le README (contexte métier agro, schéma d'architecture, comment lancer le projet, choix techniques et leurs limites).
- Week-end 2 : relire le code, nettoyer, préparer le « pitch » de 2 minutes pour un entretien et ajouter le projet à ton portfolio.

**Livrable :** un dépôt GitHub propre et une section portfolio.

---

## Pistes pour une V2 (plus tard, selon ta formation)
- Ajouter la **qualité des eaux** (nitrates, pesticides) via Hub'Eau : très parlant pour un profil agro.
- Mettre en place la CI avec GitHub Actions (tests dbt à chaque push).
- Passer dans le cloud (stockage objet et un entrepôt type BigQuery).
- Conteneuriser avec Docker.

## Suivi
| Semaine | Statut | Notions acquises | Remarques |
|---|---|---|---|
| 1 | terminée (22/11) | Lecture d'une URL d'API (paramètres, filtres optionnels), champ count, pagination (size, page, next = null en fin), clé unique code_bss, venv + requirements.txt + .gitignore, requests (params, headers, timeout, codes HTTP 4xx/5xx), json.dump vers data/brut/, full refresh idempotent, boucle while de pagination (next, garde-fou page_max, extend, contrôle len == count), code 206, débogage (print(r.url), lecture d'erreur), fonctions (def/return, variables locales), Content-Type, load.py : json.load + sqlite3 (CREATE TABLE, PRIMARY KEY, codes en TEXT, executemany avec :noms) — 6471 stations IDF chargées (INSERT OR REPLACE), 64 stations utiles après filtre ; chroniques des 64 stations extraites avec appeler_api (retry 3 essais, attente, 4xx vs 5xx), reprise via os.path.exists ; raw_chroniques chargée (clé composite code_bss + timestamp_mesure) : 634 890 mesures, contrôle COUNT = somme des fichiers avec raise ValueError ; agrégats MAX + HAVING, alias, dates ISO ; fraîcheur : 48 stations à jour, 16 sans mesure depuis plus de 30 jours | Département : Yvelines (78), 177 stations. Filtre stations utiles : `date_debut_mesure <= '2016-01-01' AND date_fin_mesure >= '2026-01-01' AND nb_mesures_piezo >= 3300` (à rendre dynamique en Python). Station test : 01825X0091/P1 (13396 mesures depuis 1972-10-10) |
| 2 | terminée (28/11) | Incrémental (MAX(date_mesure) par station, param date_debut_mesure, 1 fichier chroniques_incr_AAAA-MM-JJ.json), COUNT avant/après, HAVING, garde-fou échec silencieux, données provisoires et migration de clé (code_bss, date_mesure) avec sauvegarde et rechargement depuis le brut, module commun api_hubeau.py + docstrings, logging (niveaux, basicConfig, contexte), DuckDB (read_json_auto, glob trié, full refresh init_duckdb.py vs incrémental load.py, ATTACH SQLite + EXCEPT, CTE WITH, INTERVAL, fetchone()[0]) ; 93 mesures perdues du brut retrouvées et rattrapées (date_fin_mesure exclusive) | 635 236 mesures au 28/11, migration prouvée (EXCEPT = 0). SQLite abandonné |
| 3 | à faire | | |
| 4 | à faire | | |
| 5 | à faire | | |
