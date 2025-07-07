from typing import List
from .GetJsonFromUrl import getJsonFromUrl
from Models import (AdidasCommunity, AdidasRunnersEvent)

def getAdidasRunnersCommunityEvents(community : AdidasCommunity) -> List[AdidasRunnersEvent]:
    url = f"https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/events/communities/{community.id}?countryCodes=BR"
    data = getJsonFromUrl(url)
    virtual_events : List[AdidasRunnersEvent] = []
    for event in data["_embedded"]["events"]:
        if not event.get("meta", {}).get("adidas_runners_locations"):
            virtual_events.append(AdidasRunnersEvent(event["id"], event["title"], community.name, event["category"], event["eventStartDate"]))
    return virtual_events
