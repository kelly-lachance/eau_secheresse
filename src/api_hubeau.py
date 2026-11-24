
import requests
import time

ENTETES = {"User-Agent": "bootcamp-data/1.0 (+https://github.com/kelly-lachance)"}

def appeler_api(url, parametres) : 
    """Appelle l'API avec 3 tentatives, renvoie la réponse ou lève une erreur."""
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
    """Parcourt les pages de l'API, renvoie la liste complète des données. Lève une erreur si le nombre reçu ne correspond pas au count."""
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