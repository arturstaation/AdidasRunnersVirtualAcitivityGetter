from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService, GoogleSheetsService)
from dotenv import load_dotenv
import asyncio
import logging
from typing import List

def main():
   
    loggerService = LoggerService()
    logger = loggerService.getLogger()
    

    logging.info("Carregando Variaveis de ambiente")
    load_dotenv()

    googleSheetsService = GoogleSheetsService(logger)
    utilsService = UtilsService(logger)
    seleniumWebDriverService = SeleniumWebDriverService(logger,utilsService)
    adidasService = AdidasService(logger, seleniumWebDriverService)
    telegramService = TelegramService(logger, utilsService)



    arCommunityList = adidasService.getAdidasRunnersCommunity()
    messagesToSend : List[str] = []

    for arCommunity in arCommunityList:
        currentARCommunityEventsList = adidasService.getAdidasRunnersCommunityEvents(arCommunity)
        arCommunity.setEvents(currentARCommunityEventsList)
        googleSheetsService.add_new_activities(arCommunity)
        if(len(arCommunity.events) > 0):
            messagesToSend = telegramService.generateMessage(arCommunity, messagesToSend)

    if(len(messagesToSend) > 0):
        asyncio.run(telegramService.sendTelegramMessages(messagesToSend))
    else:
        logger.info("Nenhuma Mensagem para ser Enviada")
    seleniumWebDriverService.stopDriver()
    logger.info("Processamento Finalizado")

if __name__ == '__main__':
    main()
