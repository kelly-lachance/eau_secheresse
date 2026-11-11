
import requests
import json
stations = []  #accumule les stations de toutes les pages
URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
ENTETES = {"User-Agent": "bootcamp-data/1.0 (+https://github.com/kelly-lachance)"}

departement = 78
parametres = {"code_departement" : departement, "size" : 200}

url = URL
page = 0
page_max = 100

while page < page_max and url is not None : 
    r = requests.get(url, headers=ENTETES, timeout=10, params=parametres)
    r.raise_for_status() 
    reponse = r.json()

    stations.extend(reponse["data"])
    url = reponse["next"]
    parametres = None
    page += 1
    print(f"Nombre de page : {page}")

mon_fichier = f"data/brut/stations_{departement}.json"
with open(mon_fichier, "w", encoding="utf-8") as f:
    json.dump(stations, f, ensure_ascii=False, indent=2)

if len(stations) == reponse["count"] : 
    print(f"Le chargement des données est OK")
else : 
    print(f"Le chargement des données est NOK")