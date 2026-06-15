from Services import (AdidasService, TelegramService, LoggerService, SeleniumWebDriverService, UtilsService, PostgresService)
from dotenv import load_dotenv
import asyncio
from typing import List
import traceback
import os
import sys
import signal
import gc
import psutil

def main():
   telegramService = None
   postgresService = None
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
        utilsService.validateEnvVariables()
        telegramService = TelegramService(logger, utilsService)
        postgresService = PostgresService(logger)
        seleniumWebDriverService = SeleniumWebDriverService(logger,utilsService)
        adidasService = AdidasService(logger, seleniumWebDriverService)

        arCommunityList = adidasService.getAdidasRunnersCommunity()
        messagesToSend : List[str] = []

        for i, arCommunity in enumerate(arCommunityList):
            currentARCommunityEventsList = adidasService.getAdidasRunnersCommunityEvents(arCommunity)
            arCommunity.setEvents(currentARCommunityEventsList)
            postgresService.addNewActivities(arCommunity)
            if len(arCommunity.events) > 0:
                messagesToSend = telegramService.generateMessage(arCommunity, messagesToSend)
            arCommunity.setEvents([])
            del arCommunity
        gc.collect()


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
        if(seleniumWebDriverService is not None):
            seleniumWebDriverService.stopDriver()
        if(postgresService is not None):
            postgresService.close()
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



if __name__ == '__main__':
    result = main()
    # Sai com código != 0 quando houve erro, para que systemd/CI/wrapper de retry
    # consigam DETECTAR a falha (a state machine da AWS lia o hasError do retorno).
    sys.exit(1 if (result or {}).get("hasError") else 0)
