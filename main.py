from typing import List
from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService)
from Models import (AdidasRunnersEvent)
from dotenv import load_dotenv
import asyncio
import logging


def salvar_atividades_em_txt(events: List[AdidasRunnersEvent], nome_arquivo: str = "atividades.txt"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        for event in events:
            linha = f"id: {event.id} | nome: {event.name} | comunidade: {event.community} |categoria: {event.category} | início: {event.startDate}\n"
            f.write(linha)

def main():
   
    LoggerService()

    logging.info("Carregando Variaveis de ambiente")
    load_dotenv()

    seleniumWebDriverService = SeleniumWebDriverService()
    adidasService = AdidasService(seleniumWebDriverService)
    utilsService = UtilsService()
    telegramService = TelegramService(utilsService)

    arCommunityList = adidasService.getAdidasRunnersCommunity()
    for arCommunity in arCommunityList:
        currentARCommunityEventsList = adidasService.getAdidasRunnersCommunityEvents(arCommunity)
        salvar_atividades_em_txt(currentARCommunityEventsList)
        telegramMessage = telegramService.generateMessage(currentARCommunityEventsList, arCommunity)
        asyncio.run(telegramService.sendTelegramMessages(telegramMessage))
        break

    seleniumWebDriverService.stopDriver()

if __name__ == '__main__':
    main()
