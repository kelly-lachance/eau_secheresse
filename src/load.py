
import json
import sqlite3
from datetime import date
import os

DEPARTEMENTS_IDF = ["75", "77", "78", "91", "92", "93", "94", "95"]

conn = sqlite3.connect("data/eau_secheresse.db")

cur = conn.cursor()

cur.execute ("""
    CREATE TABLE IF NOT EXISTS raw_stations (
    code_bss TEXT PRIMARY KEY,
    date_debut_mesure DATE,
    date_fin_mesure DATE,
    code_commune_insee TEXT,
    nom_commune TEXT,
    x REAL,
    y REAL,
    altitude_station REAL,
    nb_mesures_piezo INTEGER,
    code_departement TEXT,
    nom_departement TEXT,
    profondeur_investigation REAL
    )
""")

for departement in DEPARTEMENTS_IDF : 
    print(f"Departement : {departement}")
    mon_fichier = f"data/brut/stations_{departement}.json"
    with open(mon_fichier, "r", encoding="utf-8") as f:
        stations = json.load(f)
    print(len(stations))
    cur.executemany("""INSERT OR REPLACE INTO raw_stations (code_bss,date_debut_mesure,date_fin_mesure,code_commune_insee,nom_commune,x,y,altitude_station,nb_mesures_piezo,code_departement,nom_departement,profondeur_investigation) 
    VALUES(:code_bss,:date_debut_mesure, :date_fin_mesure, :code_commune_insee, :nom_commune, :x, :y, :altitude_station, :nb_mesures_piezo, :code_departement, :nom_departement, :profondeur_investigation)""", stations)
    conn.commit()
cur.execute("SELECT COUNT(*) FROM raw_stations")
compteur = cur.fetchone()
print(f"Station chargées : {compteur[0]}")

cur.execute("""SELECT COUNT(*) FROM raw_stations
WHERE date_debut_mesure <= '2016-01-01'
  AND date_fin_mesure  >= '2026-01-01'
  AND nb_mesures_piezo >= 3300""")
nombre_stations = cur.fetchone()
print(f"Stations utiles : {nombre_stations[0]}")

cur.execute("""SELECT code_departement, COUNT(code_bss) FROM raw_stations 
WHERE date_debut_mesure <= '2016-01-01'
  AND date_fin_mesure  >= '2026-01-01'
  AND nb_mesures_piezo >= 3300
  GROUP BY code_departement""")
lien_dept_stations = cur.fetchall()
for departement, nb_stations in lien_dept_stations : 
    print(f"{departement} : {nb_stations} station(s) utile(s)")

#Chargement des données de chroniques dans la table eau_secheresse.db
STATIONS_SUIVIES = []
cur.execute("""SELECT code_bss FROM raw_stations 
WHERE date_debut_mesure <= '2016-01-01'
  AND date_fin_mesure  >= '2026-01-01'
  AND nb_mesures_piezo >= 3300""")
lignes = cur.fetchall()
for ligne in lignes :
     STATIONS_SUIVIES.append(ligne[0])
print(len(STATIONS_SUIVIES))

cur.execute ("""
    CREATE TABLE IF NOT EXISTS raw_chroniques (
    code_bss TEXT,
    date_mesure DATE,
    timestamp_mesure INT,
    niveau_nappe_eau REAL,
    qualification TEXT,
    profondeur_nappe REAL,
    PRIMARY KEY (code_bss, date_mesure)
    )
""")


cur.execute("SELECT COUNT(*) FROM raw_chroniques")
compteur_avant = cur.fetchone()
mon_fichier = f"data/brut/chroniques_incr_{date.today()}.json"
if not os.path.exists(mon_fichier) : 
    raise ValueError(f"Fichier absent : {mon_fichier}")
with open(mon_fichier, "r", encoding="utf-8") as f:
    mesures = json.load(f)
print(len(mesures))
compteur_mesure_recu =len(mesures)
cur.executemany("""INSERT OR REPLACE INTO raw_chroniques (code_bss,date_mesure,timestamp_mesure,niveau_nappe_eau,qualification,profondeur_nappe)
VALUES(:code_bss,:date_mesure,:timestamp_mesure,:niveau_nappe_eau,:qualification,:profondeur_nappe)""", mesures)
conn.commit()
cur.execute("SELECT COUNT(*) FROM raw_chroniques")
compteur_apres = cur.fetchone()
ajoutee = compteur_apres[0] - compteur_avant[0]
if 0 <= ajoutee <= compteur_mesure_recu: 
    print(f"Nouvelles chroniques chargées : {ajoutee} sur un total de {compteur_apres[0]}")
else : 
    raise ValueError(f"Le chargement est incomplet, vous avez chargé {compteur_apres} chroniques sur {compteur_avant} chroniques de départ")

      
#requête qui liste la dernière date de mesure pour chaque station
cur.execute("""SELECT code_bss, MAX(date_mesure) FROM raw_chroniques
GROUP BY code_bss""")
date_max_station = cur.fetchall()
for code_bss, derniere_date in date_max_station : 
    print(f"Dernière mesure de la station {code_bss} en date de {derniere_date}")

#requête qui ne liste que les stations dont la dernière mesure date de plus de 30 jours
cur.execute("""SELECT code_bss, MAX(date_mesure) AS derniere_mesure FROM raw_chroniques
GROUP BY code_bss
HAVING derniere_mesure < date('now' , '-30 days')""")
date_max_station = cur.fetchall()
print("Station dont la dernière mesure date de plus de 30 jours")
for code_bss, derniere_date in date_max_station : 
    print(f"Station : {code_bss} --> mesure {derniere_date}")

cur.execute("""SELECT code_bss, date_mesure, COUNT(*) as nb_lignes FROM raw_chroniques
GROUP BY code_bss, date_mesure
HAVING nb_lignes >1""")
doublon=cur.fetchall()
for code_bss, date_mesure, nb_lignes in doublon : 
    print(f"Station doublon : {code_bss} --> derniere date mesure : {date_mesure} --> nombre de doublon : {nb_lignes}")

conn.close()

