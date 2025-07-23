from logging import Logger
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
    logger : Logger

    def __init__(self: Self, logger : Logger, utilsService: UtilsService):
        self.logger = logger
        self.logger.info("Inicializando SeleniumWebDriver")
        self.utilsService = utilsService
        self.getDriver()

    def getDriver(self: Self):
        self.logger.info("Criando Selenium WebDriver")
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--headless")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
        proxyService = ProxyService(self.logger)
        proxyService.getProxies()

        self.logger.info("Gerando Proxy")
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
        self.logger.warning("Reiniciando WebDriver")
        try:
            self.stopDriver()
        except:
            pass
        self.getDriver()
    
    def getJsonFromUrl(self, url: str, tentativas: int = 3) -> dict:
        for tentativa in range(1, tentativas + 1):
            try:
                self.logger.info(f"[{tentativa}/{tentativas}] Acessando URL: {url}")
                self.driver.get(url)
                try:
                    json_text = self.driver.find_element("tag name", "pre").text
                    return json.loads(json_text)
                except NoSuchElementException:
                    self.logger.warning("Elemento <pre> não encontrado (provável erro 403)")
                    raise PermissionError("Erro 403 detectado")

            except PermissionError as e:
                self.logger.warning(f"Erro 403 detectado. Reiniciando driver... Tentativa {tentativa}")
                self.restartDriver()
            except Exception as e:
                self.logger.error(f"Erro inesperado na tentativa {tentativa}: {e}")
                self.restartDriver()

        raise Exception(f"Falha ao obter JSON de {url} após {tentativas} tentativas")
    
    def stopDriver(self: Self):
        self.logger.info("Finalizando Driver")
        self.driver.quit()