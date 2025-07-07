
from datetime import datetime
import logging

class UtilsService:
    
    @staticmethod
    def formatDate(data_iso: str) -> str:
        logging.info(f"Formatando Data {data_iso}")
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")