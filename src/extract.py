
import json
from api_hubeau import parcourir_les_pages
import logging

logging.basicConfig(
     filename="logs/pipeline.log",
     level=logging.INFO,
     format="%(asctime)s %(levelname)-8s %(message)s",
     encoding="utf-8",

)

URL_STATION = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes/stations"

DEPARTEMENTS_IDF = ["75", "77", "78", "91", "92", "93", "94", "95"]

for departement in DEPARTEMENTS_IDF : 
    print(f"Departement : {departement}")
    parametres = {"code_departement" : departement, "size" : 200}
    donnees = parcourir_les_pages(URL_STATION,parametres)
    mon_fichier = f"data/brut/stations_{departement}.json"
    with open(mon_fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)

