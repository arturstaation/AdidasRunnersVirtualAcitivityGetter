from typing import List
from Models import AdidasCommunity
from ..Selenium.GetJsonFromUrl import getJsonFromUrl
import logging

def getAdidasRunnersCommunity() -> List[AdidasCommunity]:
    url = "https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/connect/communities?limit=100&type=AdidasRunners"
    logging.info("Obtendo dados das comunidades Adidas Runners")
    data = getJsonFromUrl(url)

    arCommunityList: List[AdidasCommunity] = [] 
    logging.info("Criando lista de comunidades")
    for comunidade in data["_embedded"]["communities"]:
        id_ = comunidade["id"]
        name = comunidade["name"]
        arCommunityList.append(AdidasCommunity(id_, name))

    return arCommunityList
