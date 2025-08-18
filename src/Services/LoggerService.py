import logging
from logging import Logger
from typing import Self
import uuid
from uuid import UUID
import os

class LoggerService:

    logger : Logger
    processingId : UUID

    class SafeFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, style="%", default_processing_id="-"):
            super().__init__(fmt, datefmt, style)
            self.default_processing_id = default_processing_id

        def format(self, record):
            if not hasattr(record, "processingId"):
                record.processingId = self.default_processing_id
            return super().format(record)

    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return msg, {**kwargs, 'extra': {**kwargs.get('extra', {}), 'processingId': self.extra['processingId']}}

    def __init__(self : Self):
        self.processingId = str(uuid.uuid4())

        log_to_file = os.environ.get("LOG_TO_FILE", "")

        log_handlers = []

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = self.SafeFormatter('[%(processingId)s] - [%(asctime)s] (%(levelname)s) - %(message)s',
                          datefmt='%d-%b-%y %H:%M:%S', default_processing_id=self.processingId)
        console.setFormatter(formatter)
        log_handlers.append(console)

        logging.getLogger("seleniumwire").setLevel(logging.WARNING)
        logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
        logging.getLogger("selenium.webdriver.common.service").setLevel(logging.WARNING)
        logging.getLogger("mitmproxy").setLevel(logging.WARNING)
        logging.getLogger("hpack").setLevel(logging.WARNING)
        logging.getLogger("telegram").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("h11").setLevel(logging.WARNING)

        base_logger = logging.getLogger("Services.LoggerService")
        base_logger.setLevel(logging.DEBUG)  
        base_logger.addHandler(console)
        self.logger = self.ContextAdapter(base_logger, {'processingId': self.processingId})
        self.logger.info("Logger configurado")
        self.logger.info("Iniciando Processamento")

    def getLogger(self: Self) -> Logger:
        return self.logger
    
    def getProcessingId(self: Self) -> UUID:
        return self.processingId