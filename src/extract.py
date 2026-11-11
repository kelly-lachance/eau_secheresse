
import requests
import json
URL = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"
ENTETES = {"User-Agent": "bootcamp-data/1.0 (+https://github.com/kelly-lachance)"}

departement = 78
parametres = {"code_departement" : departement, "size" : 200}
r = requests.get(URL, headers=ENTETES, timeout=10, params=parametres)

if r.status_code != 200 : 
    raise SystemExit(f"Le serveur a répondu {r.status_code}")

reponse = r.json()

print("Nombre de stations : ", reponse["count"])
print("Nombre d'éléments dans data : ", len(reponse["data"]))
print(reponse["data"][0])

with open("data/brut/stations_78.json" , "w", encoding="utf-8") as f:
    json.dump(reponse, f, ensure_ascii=False, indent=2)