from typing import List
from Functions import (getAdidasRunnersCommunity, getAdidasRunnersCommunityEvents)
from Models import (AdidasRunnersEvent)

def salvar_atividades_em_txt(events: List[AdidasRunnersEvent], nome_arquivo: str = "atividades.txt"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        for event in events:
            linha = f"id: {event.id} | nome: {event.name} | comunidade: {event.community} |categoria: {event.category} | início: {event.startDate}\n"
            f.write(linha)


arCommunityList = getAdidasRunnersCommunity()
for arCommunity in arCommunityList:
    currentARCommunityEventsList = getAdidasRunnersCommunityEvents(arCommunity)
    salvar_atividades_em_txt(currentARCommunityEventsList)
    break

