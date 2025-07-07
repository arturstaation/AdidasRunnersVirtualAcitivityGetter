
from datetime import datetime

def formatDate(data_iso: str) -> str:
    dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y às %H:%M")