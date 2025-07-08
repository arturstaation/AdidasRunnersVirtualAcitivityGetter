import logging
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
from selenium.common.exceptions import NoSuchElementException
from typing import Self
from .UtilsService import UtilsService
from .ProxyService import ProxyService

class SeleniumWebDriverService:

    driver : webdriver
    utilsService: UtilsService

    def __init__(self: Self, utilsService: UtilsService):
        logging.info("Inicializando SeleniumWebDriver")
        self.utilsService = utilsService
        self.getDriver()

    def getDriver(self: Self):
        logging.info("Criando Selenium WebDriver")
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920x1080")
        proxyService = ProxyService()
        proxyService.getProxies()

        logging.info("Gerando Plugin de Proxy")
        proxySettings = proxyService.getProxySettings()

        proxyUrl= f"http://{proxySettings.proxyUser}:{proxySettings.proxyPassword}@{proxySettings.proxyAddress}:{proxySettings.proxyPort}"

        seleniumwireOptions = {
            "proxy":{
                "http": proxyUrl,
                "https": proxyUrl
            }
        }

        service = Service(executable_path="chromedriver.exe")
        self.driver = webdriver.Chrome(service=service ,options=options, seleniumwire_options=seleniumwireOptions)

    def restartDriver(self: Self):
        logging.warning("Reiniciando WebDriver")
        try:
            self.driver.quit()
        except:
            pass
        self.getDriver()
    
    def getJsonFromUrl(self, url: str, tentativas: int = 3) -> dict:
        for tentativa in range(1, tentativas + 1):
            try:
                logging.info(f"[{tentativa}/{tentativas}] Acessando URL: {url}")
                self.driver.get(url)
                try:
                    json_text = self.driver.find_element("tag name", "pre").text
                    return json.loads(json_text)
                except NoSuchElementException:
                    logging.warning("Elemento <pre> não encontrado (provável erro 403)")
                    raise PermissionError("Erro 403 detectado")

            except PermissionError as e:
                logging.warning(f"Erro 403 detectado. Reiniciando driver... Tentativa {tentativa}")
                self.restartDriver()
            except Exception as e:
                logging.error(f"Erro inesperado na tentativa {tentativa}: {e}")
                self.restartDriver()

        raise Exception(f"Falha ao obter JSON de {url} após {tentativas} tentativas")
    
    def stopDriver(self: Self):
        logging.info("Finalizando Driver")
        self.driver.quit()