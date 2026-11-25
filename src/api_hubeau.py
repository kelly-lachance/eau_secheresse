
import requests
import time
import logging

ENTETES = {"User-Agent": "bootcamp-data/1.0 (+https://github.com/kelly-lachance)"}

def appeler_api(url, parametres) : 
    """Appelle l'API avec 3 tentatives, renvoie la réponse ou lève une erreur."""
    for tentative in range(3) : 
        try : 
            r = requests.get(url, headers=ENTETES, timeout=60, params=parametres)
            r.raise_for_status()  
            return r
        except requests.exceptions.Timeout : 
            logging.warning(f"{url} __ {parametres} --> Tentative {tentative +1} échouée. Attendre 15s avant nouvelle tentative")
            time.sleep(15)
        except requests.exceptions.HTTPError as e :
            if e.response.status_code >= 500 : 
                logging.warning(f"{url} __ {parametres} --> le serveur a répondu par une erreur : {e}. Tentative {tentative +1} échouée. Attendre 15s avant nouvelle tentative")
                time.sleep(15)
            else : 
                logging.error(f"{url} __ {parametres} --> le serveur a répondu par une erreur {e}. Inutile de ressayer, il faut corriger")
                raise
        except requests.exceptions.RequestException as e :
            logging.warning(f"{url} __ {parametres} --> Problème réseau : {e}. Tentative {tentative +1} échouée. Attendre 15s avant nouvelle tentative")
            time.sleep(15)
    message = f"{url} __ {parametres} --> Nombre de tentative réalisée : {tentative +1}. Recommencer demain"
    logging.error(message)
    raise RuntimeError (message)


def parcourir_les_pages(url, parametres) : 
    """Parcourt les pages de l'API, renvoie la liste complète des données. Lève une erreur si le nombre reçu ne correspond pas au count."""
    page = 0
    page_max = 100
    donnees =[] #accumule les donnees de toutes les pages
    params_initiaux = parametres
    while page < page_max and url is not None :
        try :  
            r = appeler_api(url, parametres) 
            reponse = r.json()
            donnees.extend(reponse["data"])
            url = reponse["next"]
            parametres = None
            page += 1
            logging.debug(f"{params_initiaux} --> Nombre de page : {page}")
        finally : 
            time.sleep(1)

    if len(donnees) == reponse["count"] : 
        logging.info(f"{params_initiaux} --> Le chargement des données est OK : {len(donnees)} éléments reçus")
        return donnees
    else : 
        message = f"{params_initiaux} --> Chargement des données NOK, Nombre d'éléments reçues : {len(donnees)} sur un total de {reponse['count']}"
        logging.error(message)
        raise ValueError(message)