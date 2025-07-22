import os
import requests
import socket
from typing import Self
from Models import ProxyModel
from logging import Logger

class ProxyService:

    proxyUser : str
    proxyPassword : str
    proxySettings : ProxyModel
    logger : Logger

    def __init__(self: Self, logger : Logger):
        self.proxyUser = os.getenv("PROXY_USER")
        self.proxyPassword = os.getenv("PROXY_PASSWORD")
        self.proxySettings = None
        self.logger = logger

    def getProxies(self: Self, quantidade : int = 1):
        try:
            self.logger.info("Obtendo Proxy")
            proxySettings = self.getProxySettings()
            
            self.logger.info("Rotacionando IP do Proxy de Porta {proxySettings.proxyPort}")
            requests.get(f"https://{self.proxyUser}:{self.proxyPassword}@gw.dataimpulse.com:777/api/rotate_ip?port={proxySettings.proxyPort if proxySettings is not None else '10000'}")
            self.logger.info("Chamando a API para pegar obter o Proxy")
            response = requests.get(f"https://{self.proxyUser}:{self.proxyPassword}@gw.dataimpulse.com:777/api/list?format=hostname:port:login:password&quantity={int(quantidade)}&type=sticky&protocol=http&countries=br")
            proxy_data = response.text.split('\n')
            for proxy_str in proxy_data:
                self.logger.info(f"Extraindo Proxy da Request: {proxy_str}")
                proxy = proxy_str.split(":")
                
                if len(proxy) == 4:
                    try:
                        proxy[0] = socket.gethostbyname(proxy[0]) 
                        self.proxySettings = ProxyModel(proxy[0], proxy[1], proxy[2], proxy[3])
                        self.logger.info(f"Proxy obtido com sucesso")
                        return
                    except Exception as e:
                        self.logger.warning(f"Erro ao resolver proxy {proxy_str}: {e}")
                else:
                    self.logger.warning(f"Formato inválido de proxy: {proxy_str}")
        except Exception as e:
            raise Exception("Erro ao obter dados do proxy")
        
    def getProxySettings(self: Self):
        return self.proxySettings if self.proxySettings is not None else None