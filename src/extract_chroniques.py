import json
import sqlite3
import requests
import time
from datetime import date

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


cur.execute("""SELECT code_bss, MAX(date_mesure) FROM raw_chroniques
GROUP BY code_bss""")
date_max_station = cur.fetchall()
date_chroniques = {}
for code_bss, derniere_date in date_max_station :
    date_chroniques[code_bss] = derniere_date


conn.close()

def appeler_api(url, parametres) : 
    for tentative in range(3) : 
        try : 
            r = requests.get(url, headers=ENTETES, timeout=60, params=parametres)
            r.raise_for_status()  
            return r
        except requests.exceptions.Timeout : 
            print(f"Tentative {tentative +1} échouée. Attendre 15s avant nouvelle tentative")
            time.sleep(15)
        except requests.exceptions.HTTPError as e :
            if e.response.status_code >= 500 : 
                print(f"le serveur a répondu par une erreur : {e}. Tentative {tentative +1} échouée. Attendre 15s avant nouvelle tentative")
                time.sleep(15)
            else : 
                print(f"le serveur a répondu par une erreur 4xx. Inutile de ressayer, il faut corriger")
                raise
        except requests.exceptions.RequestException as e :
            print(f"Problème réseau : {e}. Tentative {tentative +1} échouée. Attendre 15s avant nouvelle tentative")
            time.sleep(15)
    raise RuntimeError(f"Nombre de tentative réalisée : {tentative +1}. Recommencer demain")




def parcourir_les_pages(url, parametres) : 
    page = 0
    page_max = 100
    donnees =[] #accumule les donnees de toutes les pages
    while page < page_max and url is not None :
        try :  
            r = appeler_api(url, parametres) 
            reponse = r.json()
            donnees.extend(reponse["data"])
            url = reponse["next"]
            parametres = None
            page += 1
            print(f"Nombre de page : {page}")
        finally : 
            time.sleep(1)

    if len(donnees) == reponse["count"] : 
        print(f"Le chargement des données est OK")
        return donnees
    else : 
        raise ValueError(f"Chargement des données NOK, Nombre d'éléments reçues : {len(donnees)} sur un total de {reponse['count']}")

nb_fichier_chronique = 0
compteur_mesure_recu = 0
for code_bss in STATIONS_SUIVIES : 
    mon_fichier_chronique = f"data/brut/chroniques_{code_bss.replace("/" , "_")}_{date.today()}.json"
    parametres_chroniques = {"code_bss" : code_bss, "size" : 1000, "date_debut_mesure" : date_chroniques[code_bss]} 
    donnees_chroniques = parcourir_les_pages(URL_CHRONIQUE,parametres_chroniques)
    compteur_mesure_recu += len(donnees_chroniques)
    with open(mon_fichier_chronique, "w", encoding="utf-8") as f:
        json.dump(donnees_chroniques, f, ensure_ascii=False, indent=2)
        nb_fichier_chronique += 1
if nb_fichier_chronique == len(STATIONS_SUIVIES): 
    print(f"Le chargement est complet, vous avez chargé {nb_fichier_chronique}  / {len(STATIONS_SUIVIES)} fichiers")
else : 
    raise ValueError(f"Le chargement est incomplet, vous avez chargé {nb_fichier_chronique} / {len(STATIONS_SUIVIES)} fichiers")

if compteur_mesure_recu != 0 : 
    print(f"Total de nouvelles données ajoutées : {compteur_mesure_recu}")
else : 
    raise ValueError(f"Problème lors du chargement des données, le compteur des chroniques est à 0 pour toutes les stations")

