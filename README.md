# Eau & sécheresse : suivi des nappes phréatiques d'Île-de-France

Pipeline de données **ELT** qui collecte chaque jour le niveau des nappes phréatiques franciliennes depuis l'API publique **Hub'Eau**. Il les historise dans une base locale et préparera des indicateurs de sécheresse consultables dans un dashboard.

> Projet personnel de data engineering, construit pas à pas. Ingénieure agronome de formation, j'ai choisi un sujet où la donnée sert directement un enjeu agricole et environnemental : la disponibilité de l'eau souterraine.

---

## Pourquoi ce projet ?

Les nappes phréatiques alimentent l'irrigation, l'eau potable et les cours d'eau en été. Suivre leur niveau dans le temps permet de repérer une sécheresse qui s'installe, bien avant qu'elle soit visible en surface. Le réseau national de piézomètres (ADES / BRGM) publie ces mesures en open data via l'API Hub'Eau. Ce projet les transforme en un jeu de données propre, historisé et mis à jour automatiquement.

## Architecture

```
API Hub'Eau (piézométrie) ─┐
                           ├─> Python (extract + load) ─> SQLite  (DuckDB en semaine 2)
API Open-Meteo (pluie)  ───┘          │                       │
   (à venir)                          │              dbt : staging -> marts + tests
                    orchestration Prefect (quotidienne)       │   (DuckDB local + Snowflake)
                                                     dashboard Streamlit
```

Principe **ELT** : on stocke d'abord la donnée **brute**, telle que l'API la renvoie (fichiers JSON puis tables `raw_*`), et on ne la transforme qu'ensuite. Si une règle de calcul change, il suffit de rejouer la transformation sans réinterroger l'API.

## Avancement

| Étape | Statut |
|---|---|
| 1. Exploration de l'API, extraction et chargement brut | ✅ terminé (22/11/2026) |
| 2. Ingestion fiable et incrémentale, migration vers DuckDB | 🔄 en cours |
| 3. Transformations dbt (staging, faits/dimensions, tests), cible Snowflake | ⏳ à venir |
| 4. Croisement avec la météo (Open-Meteo), orchestration Prefect | ⏳ à venir |
| 5. Dashboard Streamlit | ⏳ à venir |

## Les données en chiffres (au 22/11/2026)

- **6 471 stations** piézométriques référencées en Île-de-France (8 départements).
- **64 stations retenues** pour le suivi : un historique d'au moins 10 ans, encore actives en 2026 et au moins 3 300 mesures.
- **634 890 mesures** journalières chargées. Certaines séries remontent à plus de 50 ans, comme celle de la station 01825X0091/P1 à Mareil-le-Guyon (78), suivie depuis 1972.

| Département | Stations référencées | Stations retenues |
|---|---:|---:|
| 75 Paris | 2 069 | 1 |
| 77 Seine-et-Marne | 1 256 | 35 |
| 78 Yvelines | 177 | 11 |
| 91 Essonne | 146 | 11 |
| 92 Hauts-de-Seine | 1 053 | 0 |
| 93 Seine-Saint-Denis | 707 | 0 |
| 94 Val-de-Marne | 623 | 0 |
| 95 Val-d'Oise | 440 | 6 |

Paris et la petite couronne comptent beaucoup de stations, mais presque aucune ne passe le filtre. Il s'agit probablement de points de mesure ponctuels (chantiers, études), dont l'historique est trop court ou interrompu. C'est pourquoi la grande couronne concentre les stations retenues.

## Ce qui est en place

### Extraction (`src/extract.py`, `src/extract_chroniques.py`)
- Appels à l'API Hub'Eau avec `requests` : paramètres, en-tête `User-Agent` et délai d'attente maximal (timeout).
- **Pagination** complète : on suit le lien `next` jusqu'à `null`, avec un garde-fou sur le nombre maximal de pages.
- **Relances automatiques** (`appeler_api`) : 3 tentatives espacées de 15 s en cas de timeout, d'erreur serveur 5xx ou de problème réseau. Une erreur 4xx arrête tout de suite le script, car c'est la requête qu'il faut corriger.
- **Contrôles qualité** : le nombre de lignes reçues doit égaler le `count` annoncé par l'API, et le nombre de fichiers produits doit égaler le nombre de stations suivies.
- Les réponses brutes sont sauvegardées en JSON dans `data/brut/` (non versionné).
- **Mode incrémental** : pour chaque station, le script lit en base la date de la dernière mesure (`MAX(date_mesure)`) et ne demande à l'API que les mesures à partir de cette date. Chaque passage écrit un fichier daté (`chroniques_<station>_<AAAA-MM-JJ>.json`), ce qui conserve l'historique brut intact.
- **Garde-fou contre l'échec silencieux** : si aucune des 64 stations ne renvoie de mesure, le script s'arrête en erreur au lieu d'afficher « OK ».

### Chargement (`src/load.py`)
- Base SQLite `data/eau_secheresse.db` avec deux tables brutes :
  - `raw_stations` : clé primaire `code_bss` ;
  - `raw_chroniques` : **clé primaire composite** (`code_bss`, `timestamp_mesure`).
- Chargement **idempotent** avec `INSERT OR REPLACE` : relancer le script ne crée jamais de doublon.
- Requêtes paramétrées (`executemany` avec des paramètres nommés), ce qui protège contre l'injection SQL.
- La liste des stations suivies est **calculée en SQL** à partir de `raw_stations`, et non écrite en dur.
- **Contrôle du chargement incrémental** : un `COUNT` avant et après le chargement, avec la vérification `0 ≤ lignes ajoutées ≤ mesures reçues`. Les stations sans fichier du jour sont signalées et comptées sans arrêter le traitement.

## Ce que les données ont déjà montré

**Fraîcheur des données.** Au 22/11/2026, 48 stations ont une mesure datée de moins de 5 jours. 15 stations sont figées à la mi-septembre, la plupart à la même date, ce qui suggère un réseau qui transmet par lots. Une dernière station est muette depuis juin. Un dashboard devra afficher la date de dernière mesure pour qu'une station silencieuse ne passe pas pour une nappe stable.

**Fiabilité de la source.** L'API a connu deux incidents pendant le développement. Le 18/11, elle renvoyait une page HTML d'erreur avec un code 200. Le 22/11, l'endpoint `/chroniques` renvoyait 0 résultat pour toutes les stations de France, alors que `/stations` fonctionnait. Ces incidents ont motivé les relances automatiques et le garde-fou contre l'échec silencieux.

## Lancer le projet

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python src/extract.py            # 1. stations d'Île-de-France -> data/brut/
python src/load.py               # 2. chargement de raw_stations
python src/extract_chroniques.py # 3. mesures des 64 stations suivies
python src/load.py               # 4. chargement de raw_chroniques
```

Les étapes dépendent les unes des autres : la liste des stations suivies vient de `raw_stations`, et la date de reprise de l'incrémental vient de `raw_chroniques`. Cet enchaînement sera confié à un orchestrateur (Prefect) en semaine 4.

## Choix techniques

| Choix | Pourquoi |
|---|---|
| Stockage du JSON brut avant chargement | Rejouer le chargement sans réinterroger l'API, et garder une trace de ce que la source a réellement renvoyé |
| Clé composite `code_bss` + `timestamp_mesure` | Une mesure est unique pour une station à un instant donné : c'est ce qui rend l'idempotence possible |
| Incrémental qui repart de la **dernière date** (et non du lendemain) | Récupérer une éventuelle correction de la dernière mesure ; le doublon est absorbé par `INSERT OR REPLACE` |
| Dates au format ISO `AAAA-MM-JJ` | L'ordre alphabétique correspond à l'ordre chronologique, donc `MAX()` et les comparaisons fonctionnent sur du texte |
| SQLite pour démarrer, DuckDB ensuite | SQLite pour apprendre les bases sans serveur ; DuckDB, base orientée colonnes, pour l'analytique |
| DuckDB en local, Snowflake comme seconde cible dbt | Découvrir un entrepôt cloud tout en gardant un projet qui fonctionne gratuitement en local |

## Limites connues et prochaines étapes

- La fonction `parcourir_les_pages` est copiée dans deux scripts : il faudra la factoriser dans un module commun.
- Les `print` seront remplacés par de vrais **logs** (module `logging`).
- Le contrôle final compare la table entière : si une station sort un jour du filtre, ses anciennes mesures restent en base. Ce cas sera géré dans la couche dbt.
- Migration de SQLite vers DuckDB, puis transformations dbt (staging, `dim_stations`, `fct_niveaux_journaliers`, indicateur d'écart à la normale saisonnière).

## Sources

- [Hub'Eau, API Piézométrie](https://hubeau.eaufrance.fr/page/api-piezometrie) : données ADES / BRGM, licence ouverte Etalab.
- [Open-Meteo](https://open-meteo.com/) (à venir) : précipitations et évapotranspiration.
