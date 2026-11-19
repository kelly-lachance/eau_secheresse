
import requests
import json
import time

URL_STATION = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
ENTETES = {"User-Agent": "bootcamp-data/1.0 (+https://github.com/kelly-lachance)"}
DEPARTEMENTS_IDF = ["75", "77", "78", "91", "92", "93", "94", "95"]



def parcourir_les_pages(url, parametres) : 
    page = 0
    page_max = 100
    donnees =[] #accumule les donnees de toutes les pages
    while page < page_max and url is not None :
        try :  
            r = requests.get(url, headers=ENTETES, timeout=10, params=parametres)
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

for departement in DEPARTEMENTS_IDF : 
    print(f"Departement : {departement}")
    parametres = {"code_departement" : departement, "size" : 200}
    donnees = parcourir_les_pages(URL_STATION,parametres)
    mon_fichier = f"data/brut/stations_{departement}.json"
    with open(mon_fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)

