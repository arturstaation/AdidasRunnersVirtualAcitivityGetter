import os
import requests
import socket
from typing import Self
from Models import ProxyModel
import logging

class ProxyService:

    proxyUser : str
    proxyPassword : str
    proxySettings : ProxyModel

    def __init__(self: Self):
        self.proxyUser = os.getenv("PROXY_USER")
        self.proxyPassword = os.getenv("PROXY_PASSWORD")
        self.proxySettings = None

    def getProxies(self: Self, quantidade : int = 1):
        try:
            logging.info("Obtendo Proxy")
            proxySettings = self.getProxySettings()
            
            logging.info("Rotacionando IP do Proxy de Porta {proxySettings.proxyPort}")
            requests.get(f"https://{self.proxyUser}:{self.proxyPassword}@gw.dataimpulse.com:777/api/rotate_ip?port={proxySettings.proxyPort if proxySettings is not None else '10000'}")
            logging.info("Chamando a API para pegar obter o Proxy")
            response = requests.get(f"https://{self.proxyUser}:{self.proxyPassword}@gw.dataimpulse.com:777/api/list?format=hostname:port:login:password&quantity={int(quantidade)}&type=sticky&protocol=http&countries=br")
            proxy_data = response.text.split('\n')
            for proxy_str in proxy_data:
                logging.info(f"Extraindo Proxy da Request: {proxy_str}")
                proxy = proxy_str.split(":")
                
                if len(proxy) == 4:
                    try:
                        proxy[0] = socket.gethostbyname(proxy[0]) 
                        self.proxySettings = ProxyModel(proxy[0], proxy[1], proxy[2], proxy[3])
                        logging.info(f"Proxy obtido com sucesso")
                        return
                    except Exception as e:
                        logging.warning(f"Erro ao resolver proxy {proxy_str}: {e}")
                else:
                    logging.warning(f"Formato inválido de proxy: {proxy_str}")
        except:
            raise Exception("Erro ao obter dados do proxy")
        
    def getProxySettings(self: Self):
        return self.proxySettings if self.proxySettings is not None else None