import logging
from Models import (AdidasCommunity, AdidasRunnersEvent)
from typing import List, Self
from .SeleniumWebDriverService import SeleniumWebDriverService

class AdidasService:
    seleniumWebDriverService : SeleniumWebDriverService

    def __init__(self: Self, seleniumWebDriverService: SeleniumWebDriverService):
        self.seleniumWebDriverService = seleniumWebDriverService

    def getAdidasRunnersCommunity(self: Self) -> List[AdidasCommunity]:
        url = "https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/connect/communities?limit=100&type=AdidasRunners"
        logging.info("Obtendo dados das comunidades Adidas Runners")
        data = self.seleniumWebDriverService.getJsonFromUrl(url)

        arCommunityList: List[AdidasCommunity] = [] 
        logging.info("Criando lista de comunidades")
        for comunidade in data["_embedded"]["communities"]:
            id_ = comunidade["id"]
            name = comunidade["name"]
            arCommunityList.append(AdidasCommunity(id_, name))

        return arCommunityList

    def getAdidasRunnersCommunityEvents(self: Self, community : AdidasCommunity) -> List[AdidasRunnersEvent]:
        url = f"https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/events/communities/{community.id}?countryCodes=BR"
        logging.info(f"Obtendo dados Eventos da Comunidade {community.name}")
        data = self.seleniumWebDriverService.getJsonFromUrl(url)
        virtual_events : List[AdidasRunnersEvent] = []
        
        logging.info(f"Criando Lista de Eventos da Comunidade {community.name}")
        for event in data["_embedded"]["events"]:
            if not event.get("meta", {}).get("adidas_runners_locations"):
                virtual_events.append(AdidasRunnersEvent(event["id"], event["title"], community.name, event["category"], event["eventStartDate"]))
        return virtual_events