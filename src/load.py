
from datetime import date
import os
import logging
import duckdb


logging.basicConfig(
     filename="logs/pipeline.log",
     level=logging.INFO,
     format="%(asctime)s %(levelname)-8s %(message)s",
     encoding="utf-8",
)


con = duckdb.connect("data/eau_secheresse.duckdb")


con.execute ("""
    CREATE TABLE IF NOT EXISTS raw_stations (
    code_bss TEXT PRIMARY KEY,
    date_debut_mesure DATE,
    date_fin_mesure DATE,
    code_commune_insee TEXT,
    nom_commune TEXT,
    x DOUBLE,
    y DOUBLE,
    altitude_station DOUBLE,
    nb_mesures_piezo INTEGER,
    code_departement TEXT,
    nom_departement TEXT,
    profondeur_investigation DOUBLE
    )
""")

con.execute("""INSERT OR REPLACE INTO raw_stations 
                SELECT code_bss,date_debut_mesure,date_fin_mesure,code_commune_insee,nom_commune,x,y,altitude_station,nb_mesures_piezo,code_departement,nom_departement,profondeur_investigation
                FROM read_json_auto('data/brut/stations_*.json')""")
con.execute("SELECT COUNT(*) FROM raw_stations")
compteur = con.fetchone()
logging.info(f"Nombre de stations chargées dans la base : {compteur[0]}")


con.execute("""SELECT code_departement, COUNT(code_bss) FROM raw_stations 
WHERE date_debut_mesure <= '2016-01-01'
  AND date_fin_mesure  >= '2026-01-01'
  AND nb_mesures_piezo >= 3300
  GROUP BY code_departement""")
lien_dept_stations = con.fetchall()
for departement, nb_stations in lien_dept_stations : 
    logging.info(f"{departement} : {nb_stations} station(s) utile(s)")

#Chargement incrémental des données de chroniques dans la table eau_secheresse.duckdb
con.execute ("""
    CREATE TABLE IF NOT EXISTS raw_chroniques (
    code_bss TEXT,
    date_mesure DATE,
    timestamp_mesure BIGINT,
    niveau_nappe_eau DOUBLE,
    qualification TEXT,
    profondeur_nappe DOUBLE,
    PRIMARY KEY (code_bss, date_mesure)
    )
""")

con.execute("SELECT COUNT(*) FROM raw_chroniques")
compteur_avant = con.fetchone()[0]
mon_fichier = f"data/brut/chroniques_incr_{date.today()}.json"
if not os.path.exists(mon_fichier) : 
    message = f"Fichier absent : {mon_fichier}"
    logging.error(message)
    raise ValueError(message)
con.execute(f"SELECT COUNT(*) FROM read_json_auto('{mon_fichier}')")
nb_recues = con.fetchone()[0]
logging.info(f"Nombre chronique du fichier {mon_fichier} à ajouter dans la base : {nb_recues}")
con.execute(f"""INSERT OR REPLACE INTO raw_chroniques
                SELECT code_bss,date_mesure,timestamp_mesure,niveau_nappe_eau,qualification,profondeur_nappe
                FROM read_json_auto('{mon_fichier}')""")
con.execute("SELECT COUNT(*) FROM raw_chroniques")
compteur_apres = con.fetchone()[0]
ajoutee = compteur_apres - compteur_avant
if 0 <= ajoutee <= nb_recues : 
    logging.info(f"Nouvelles chroniques chargées : {nb_recues} reçues, {ajoutee} ajoutées, {nb_recues - ajoutee} remplacées (chevauchements), total de {compteur_apres}")
else : 
    message = f"Le chargement est incomplet, vous avez chargé {ajoutee} chroniques sur {nb_recues} chroniques de départ"
    logging.error(message)
    raise ValueError(message)

      
#requête qui liste la dernière date de mesure pour chaque station
con.execute("""SELECT code_bss, MAX(date_mesure) FROM raw_chroniques
GROUP BY code_bss""")
date_max_station = con.fetchall()
for code_bss, derniere_date in date_max_station : 
    logging.debug(f"Dernière mesure de la station {code_bss} en date de {derniere_date}")

#requête qui ne liste que les stations dont la dernière mesure date de plus de 30 jours
con.execute("""SELECT code_bss, MAX(date_mesure) AS derniere_mesure FROM raw_chroniques
GROUP BY code_bss
HAVING derniere_mesure < current_date - INTERVAL 30 DAY""")
date_max_station = con.fetchall()
for code_bss, derniere_date in date_max_station : 
    logging.warning(f"stations dont la dernière mesure date de plus de 30 jours : {code_bss} --> mesure {derniere_date}")

con.close()

