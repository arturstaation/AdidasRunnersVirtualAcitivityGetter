
from datetime import datetime
from logging import Logger
from typing import Self, Iterable, Dict, Optional, List
import os

class UtilsService:

    logger : Logger
    def __init__(self : Self, logger : Logger):
        self.logger = logger
    
    def formatDate(self: Self, data_iso: str) -> str:
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")
    
    def strToBool(self: Self, s: str) -> bool:
        return s.strip().lower() in ("1", "true", "t", "yes", "y", "on")
    
    def validateEnvVariables(self: Self) -> None:
        missing: List[str] = []

        requiredVars: Iterable[str] = (
            "GOOGLE_CREDENTIALS",
            "GOOGLE_SHEET_ID",
            "TOKEN",
            "CHAT_ID",
        )

        env: Dict[str, Optional[str]] = {k: os.getenv(k) for k in set(requiredVars) | {
            "ADMIN_CHAT_ID", "AGENT", "PROXY_USER", "PROXY_PASSWORD", "PROXY_LINK", "PROXY_PORT"
        }}

        for var in requiredVars:
            val = env.get(var)
            if val is None or str(val).strip() == "":
                missing.append(var)

        adminChatId = env.get("ADMIN_CHAT_ID")
        if not adminChatId or str(adminChatId).strip() == "":
            if getattr(self, "logger", None):
                self.logger.warning("ADMIN_CHAT_ID (Chat de Administrador) não configurado")

        agent = env.get("AGENT")
        if not agent or str(agent).strip() == "":
            if getattr(self, "logger", None):
                self.logger.warning("AGENT não configurado, será usado o valor padrão configurado no serviço")

        proxyEnabled = self.strToBool(os.getenv("PROXY_ENABLED", "False"))
        if proxyEnabled:
            if not env.get("PROXY_USER") or str(env.get("PROXY_USER")).strip() == "":
                missing.append("PROXY_USER")
            if not env.get("PROXY_PASSWORD") or str(env.get("PROXY_PASSWORD")).strip() == "":
                missing.append("PROXY_PASSWORD")
            if not env.get("PROXY_LINK") or str(env.get("PROXY_LINK")).strip() == "":
                missing.append("PROXY_LINK")
            if not env.get("PROXY_PORT") or str(env.get("PROXY_PORT")).strip() == "":
                missing.append("PROXY_PORT")
        else:
            
            self.logger.warning("Proxy desabilitado")

        if missing:
            missingSorted = ", ".join(sorted(set(missing)))
            raise Exception(f"As seguintes variáveis de ambiente não estão configuradas: {missingSorted}")