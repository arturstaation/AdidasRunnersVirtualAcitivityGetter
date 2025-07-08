from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService)
from Models import (AdidasCommunity)
from dotenv import load_dotenv
import asyncio
import logging


def salvar_atividades_em_txt(arCommunity: AdidasCommunity, nome_arquivo: str = "atividades.txt"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        for event in arCommunity.events:
            linha = f"id: {event.id} | nome: {event.name} | comunidade: {arCommunity.name} |categoria: {event.category} | início: {event.startDate}\n"
            f.write(linha)

def main():
   
    LoggerService()

    logging.info("Carregando Variaveis de ambiente")
    load_dotenv()

    utilsService = UtilsService()
    seleniumWebDriverService = SeleniumWebDriverService(utilsService)
    adidasService = AdidasService(seleniumWebDriverService)
    telegramService = TelegramService(utilsService)

    arCommunityList = adidasService.getAdidasRunnersCommunity()
    for arCommunity in arCommunityList:
        currentARCommunityEventsList = adidasService.getAdidasRunnersCommunityEvents(arCommunity)
        arCommunity.setEvents(currentARCommunityEventsList)
        salvar_atividades_em_txt(arCommunity)
        telegramMessage = telegramService.generateMessage(arCommunity)
        asyncio.run(telegramService.sendTelegramMessages(telegramMessage))

    seleniumWebDriverService.stopDriver()

if __name__ == '__main__':
    main()
