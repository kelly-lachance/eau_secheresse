
import json
import sqlite3
DEPARTEMENTS_IDF = ["78"]

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
conn.close()   