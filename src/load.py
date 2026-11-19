
import json
import sqlite3
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

conn.close()

