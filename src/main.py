from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService, GoogleSheetsService)
from dotenv import load_dotenv
import asyncio
from typing import List
import traceback

def main():
   loggerService = LoggerService()
   logger = loggerService.getLogger()
   utilsService = UtilsService(logger)
   logger.info("Carregando Variaveis de ambiente")  
   load_dotenv()
   try:
        telegramService = TelegramService(logger, utilsService)
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
        empty = False
        if(len(messagesToSend) > 0):
            asyncio.run(telegramService.sendTelegramMessages(messagesToSend))
        else:
            empty = True
            logger.info("Nenhuma Mensagem para ser Enviada")

        admMessage = telegramService.generateAdminSuccessMessage(loggerService.getProcessingId(), empty)
        asyncio.run(telegramService.sendTelegramAdminMessage(admMessage))

   except Exception as e:
    telegramService = TelegramService(logger, utilsService)
    stacktrace = traceback.format_exc()
    logger.error(f"Erro durante o processamento! Erro: {e}. Stacktrace: {stacktrace}")
    errorMessage = telegramService.generateAdminErrorMessage(loggerService.getProcessingId(), e, stacktrace)
    asyncio.run(telegramService.sendTelegramAdminMessage(errorMessage))
   finally:
        seleniumWebDriverService.stopDriver()
        logger.info("Processamento Finalizado")
       
       

if __name__ == '__main__':
    main()
