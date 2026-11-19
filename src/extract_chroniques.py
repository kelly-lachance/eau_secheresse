import json
import sqlite3
import requests
import time
import os

conn = sqlite3.connect("data/eau_secheresse.db")
cur = conn.cursor()
URL_CHRONIQUE = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/chroniques"
STATIONS_SUIVIES = []
ENTETES = {"User-Agent": "bootcamp-data/1.0 (+https://github.com/kelly-lachance)"}

cur.execute("""SELECT code_bss FROM raw_stations 
WHERE date_debut_mesure <= '2016-01-01'
  AND date_fin_mesure  >= '2026-01-01'
  AND nb_mesures_piezo >= 3300""")
lignes = cur.fetchall()
for ligne in lignes :
     STATIONS_SUIVIES.append(ligne[0])
print(len(STATIONS_SUIVIES))

conn.close()


def parcourir_les_pages(url, parametres) : 
    page = 0
    page_max = 100
    donnees =[] #accumule les donnees de toutes les pages
    while page < page_max and url is not None :
        try :  
            r = requests.get(url, headers=ENTETES, timeout=60, params=parametres)
            r.raise_for_status() 
            reponse = r.json()

            donnees.extend(reponse["data"])
            url = reponse["next"]
            parametres = None
            page += 1
            print(f"Nombre de page : {page}")
        except requests.exceptions.Timeout : 
            print("C'est trop lent, on s'arrête là")
            raise
        except requests.exceptions.HTTPError as e :
            print(f"le serveur a répondu par une erreur : {e}")
            raise
        except requests.exceptions.RequestException as e :
            print(f"Problème réseau : {e}")
            raise
        finally : 
            time.sleep(1)

    if len(donnees) == reponse["count"] : 
        print(f"Le chargement des données est OK")
        return donnees
    else : 
        raise ValueError(f"Chargement des données NOK, Nombre d'éléments reçues : {len(donnees)} sur un total de {reponse['count']}")


for code_bss in STATIONS_SUIVIES : 
    mon_fichier_chronique = f"data/brut/chroniques_{code_bss.replace("/" , "_")}.json"
    if os.path.exists(mon_fichier_chronique) :
        print(f"Déjà présent on passe : {code_bss}") 
        continue
    parametres_chroniques = {"code_bss" : code_bss, "size" : 1000}
    donnees_chroniques = parcourir_les_pages(URL_CHRONIQUE,parametres_chroniques)
    with open(mon_fichier_chronique, "w", encoding="utf-8") as f:
        json.dump(donnees_chroniques, f, ensure_ascii=False, indent=2)