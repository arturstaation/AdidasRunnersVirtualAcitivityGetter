from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService, GoogleSheetsService)
from dotenv import load_dotenv
import asyncio
from typing import List
import traceback

def main():
   loggerService = LoggerService()
   logger = loggerService.getLogger()
   load_dotenv()
   logger.info("Carregando Variaveis de ambiente")  
   utilsService = UtilsService(logger)
   telegramService = TelegramService(logger, utilsService)
   try:
        googleSheetsService = GoogleSheetsService(logger)
        seleniumWebDriverService = SeleniumWebDriverService(logger,utilsService)
        adidasService = AdidasService(logger, seleniumWebDriverService)



        arCommunityList = adidasService.getAdidasRunnersCommunity()
        messagesToSend : List[str] = []

        for arCommunity in arCommunityList:
            currentARCommunityEventsList = adidasService.getAdidasRunnersCommunityEvents(arCommunity)
            arCommunity.setEvents(currentARCommunityEventsList)
            googleSheetsService.addNewActivities(arCommunity)
            if(len(arCommunity.events) > 0):
                messagesToSend = telegramService.generateMessage(arCommunity, messagesToSend)

        if(len(messagesToSend) > 0):
            asyncio.run(telegramService.sendTelegramMessages(messagesToSend))
        else:
            logger.info("Nenhuma Mensagem para ser Enviada")
        seleniumWebDriverService.stopDriver()
        logger.info("Processamento Finalizado")
   except Exception as e:
    stacktrace = traceback.format_exc()
    logger.error(f"Erro durante o processamento! Erro: {e}. Stacktrace: {stacktrace}")
    errorMessage = telegramService.generateAdminErrorMessage(loggerService.getProcessingId(), e, stacktrace)
    asyncio.run(telegramService.sendTelegramAdminMessage(errorMessage))
       
       

if __name__ == '__main__':
    main()
