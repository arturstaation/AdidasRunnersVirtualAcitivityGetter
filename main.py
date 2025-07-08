from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService)
from Models import (AdidasCommunity)
from dotenv import load_dotenv
import asyncio
import logging
from typing import List

def main():
   
    LoggerService()

    logging.info("Carregando Variaveis de ambiente")
    load_dotenv()

    utilsService = UtilsService()
    seleniumWebDriverService = SeleniumWebDriverService(utilsService)
    adidasService = AdidasService(seleniumWebDriverService)
    telegramService = TelegramService(utilsService)

    arCommunityList = adidasService.getAdidasRunnersCommunity()
    messagesToSend : List[str] = []

    for arCommunity in arCommunityList:
        currentARCommunityEventsList = adidasService.getAdidasRunnersCommunityEvents(arCommunity)
        arCommunity.setEvents(currentARCommunityEventsList)
        if(len(currentARCommunityEventsList) > 0):
            messagesToSend = telegramService.generateMessage(arCommunity, messagesToSend)

    if(len(messagesToSend) > 0):
        asyncio.run(telegramService.sendTelegramMessages(messagesToSend))
    else:
        logging.info("Nenhuma Mensagem para ser Enviada")
    seleniumWebDriverService.stopDriver()

if __name__ == '__main__':
    main()
