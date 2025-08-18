from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService, GoogleSheetsService)
from dotenv import load_dotenv
import asyncio
from typing import List
import traceback
import os
import signal
import psutil

def main():
   telegramService = None
   googleSheetsService = None
   seleniumWebDriverService = None
   adidasService = None
   loggerService = None
   logger = None
   utilsService = None
   try:
        loggerService = LoggerService()
        logger = loggerService.getLogger()
        logger.info("Carregando Variaveis de ambiente")  
        load_dotenv()
        utilsService = UtilsService(logger)
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
        return {
            "hasError": False,
            "message": f"O processamento ocorreu com sucesso. {'Novos eventos foram encontrados' if not empty else 'Nenhum novo evento foi encontrado'}"
        }

   except Exception as e:
    telegramService = TelegramService(logger, utilsService)
    stacktrace = traceback.format_exc()
    logger.error(f"Erro durante o processamento! Erro: {e}. Stacktrace: {stacktrace}")
    errorMessage = telegramService.generateAdminErrorMessage(loggerService.getProcessingId(), e, stacktrace)
    asyncio.run(telegramService.sendTelegramAdminMessage(errorMessage))
    return {
        "hasError": True,
        "error": str(e),
        "message": "Ocorreu um erro durante o processamento"
    }
   finally:
        seleniumWebDriverService.stopDriver()
        logger.info("Processamento Finalizado")
        try:
            try:
                parent = psutil.Process(os.getpid())
            except psutil.NoSuchProcess:
                return
            children = parent.children(recursive=True)
            for process in children:
                try:
                    process.send_signal(signal.SIGTERM)
                except Exception:
                    pass
        except Exception as e:
            if logger:
                logger.warning(f"Erro ao matar processos filhos: {e}")

        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass

       
       
def lambda_handler(event, context):
    return main()

if __name__ == '__main__':
    main()
