import json
import sqlite3
from datetime import date
from api_hubeau import appeler_api, parcourir_les_pages
import logging

logging.basicConfig(
     filename="logs/pipeline.log",
     level=logging.INFO,
     format="%(asctime)s %(levelname)-8s %(message)s",
     encoding="utf-8",

)

conn = sqlite3.connect("data/eau_secheresse.db")
cur = conn.cursor()
URL_CHRONIQUE = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
STATIONS_SUIVIES = []

cur.execute("""SELECT code_bss FROM raw_stations 
WHERE date_debut_mesure <= '2016-01-01'
  AND date_fin_mesure  >= '2026-01-01'
  AND nb_mesures_piezo >= 3300""")
lignes = cur.fetchall()
for ligne in lignes :
     STATIONS_SUIVIES.append(ligne[0])
logging.info(f"{len(STATIONS_SUIVIES)} stations suivies")


cur.execute("""SELECT code_bss, MAX(date_mesure) FROM raw_chroniques
GROUP BY code_bss""")
date_max_station = cur.fetchall()
date_chroniques = {}
for code_bss, derniere_date in date_max_station :
    date_chroniques[code_bss] = derniere_date

conn.close()


mesures_stations = []
nb_stations_interrogees = 0
for code_bss in STATIONS_SUIVIES : 
    parametres_chroniques = {"code_bss" : code_bss, "size" : 1000, "date_debut_mesure" : date_chroniques[code_bss]} 
    donnees_chroniques = parcourir_les_pages(URL_CHRONIQUE,parametres_chroniques)
    mesures_stations.extend(donnees_chroniques)
    nb_stations_interrogees+= 1
if nb_stations_interrogees == len(STATIONS_SUIVIES): 
    logging.info(f"Le chargement est complet, vous avez chargé {nb_stations_interrogees}  / {len(STATIONS_SUIVIES)} stations")
else : 
    message = f"Le chargement est incomplet, vous avez chargé {nb_stations_interrogees} / {len(STATIONS_SUIVIES)} stations"
    logging.error(message)
    raise ValueError(message)

if len(mesures_stations) != 0 : 
    logging.info(f"Total de nouvelles données reçues : {len(mesures_stations)}")
else : 
    message = f"Problème lors du chargement des données, le compteur des chroniques est à 0 pour toutes les stations"
    logging.error(message)
    raise ValueError(message)

mon_fichier_chronique = f"data/brut/chroniques_incr_{date.today()}.json"
with open(mon_fichier_chronique, "w", encoding="utf-8") as f:
        json.dump(mesures_stations, f, ensure_ascii=False, indent=2)
logging.info(f"Données écrites dans {mon_fichier_chronique}")
