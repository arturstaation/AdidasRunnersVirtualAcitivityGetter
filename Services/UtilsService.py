
from datetime import datetime
from logging import Logger
from typing import Self

class UtilsService:
    
    logger : Logger
    def __init__(self : Self, logger : Logger):
        self.logger = logger

    def formatDate(self: Self, data_iso: str) -> str:
        self.logger.info(f"Formatando Data {data_iso}")
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")