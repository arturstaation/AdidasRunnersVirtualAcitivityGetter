import logging
from logging import Logger
from typing import Self
import uuid
from uuid import UUID

class LoggerService:

    logger : Logger
    processingId : UUID

    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return msg, {**kwargs, 'extra': {**kwargs.get('extra', {}), 'processingId': self.extra['processingId']}}

    def __init__(self : Self):
        
        self.processingId = str(uuid.uuid4())
        logging.basicConfig(
            level=logging.DEBUG,
            filename="application.log", 
            filemode="a", 
            format='[%(asctime)s] (%(levelname)s) - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S'
        )
        
        logging.getLogger("seleniumwire").setLevel(logging.WARNING)

        logging.getLogger("mitmproxy").setLevel(logging.WARNING)
        logging.getLogger("hpack").setLevel(logging.WARNING)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(processingId)s] - [%(asctime)s] (%(levelname)s) - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        console.setFormatter(formatter)
        base_logger = logging.getLogger(__name__)
        base_logger.addHandler(console)
        self.logger = self.ContextAdapter(base_logger, {'processingId': self.processingId})
        self.logger.info("Logger configurado")
        self.logger.info("Iniciando Processamento")

    def getLogger(self: Self) -> Logger:
        return self.logger
    
    def getProcessingId(self: Self) -> UUID:
        return self.processingId
        