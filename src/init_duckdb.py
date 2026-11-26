import duckdb
import logging
import glob

logging.basicConfig(
     filename="logs/pipeline.log",
     level=logging.INFO,
     format="%(asctime)s %(levelname)-8s %(message)s",
     encoding="utf-8",
)

con = duckdb.connect("data/eau_secheresse.duckdb")

#Chargement des stations dans la table eau_secheresse.duckdb
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


#Chargement des données de chroniques dans la table eau_secheresse.duckdb
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

Liste_historique = sorted(glob.glob("data/brut/chroniques_0*.json"))
Liste_incr = sorted(glob.glob("data/brut/chroniques_incr_*.json"))
Liste_final_fichiers_chroniques = Liste_historique + Liste_incr
con.execute("SELECT COUNT(*) FROM raw_chroniques")
compteur_avant = con.fetchone()
for fichier_chronique in Liste_final_fichiers_chroniques : 
    con.execute(f"""INSERT OR REPLACE INTO raw_chroniques
                SELECT code_bss,date_mesure,timestamp_mesure,niveau_nappe_eau,qualification,profondeur_nappe
                FROM read_json_auto('{fichier_chronique}')""")
con.execute("SELECT COUNT(*) FROM raw_chroniques")
compteur_apres = con.fetchone()
ajoutee = compteur_apres[0] - compteur_avant[0]
logging.info(f"Nouvelles chroniques chargées : {ajoutee} sur un total de {compteur_apres[0]}")


