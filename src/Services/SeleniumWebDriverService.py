from logging import Logger
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import Self
from .UtilsService import UtilsService
from .ProxyService import ProxyService
import traceback
import sys
from tempfile import mkdtemp

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
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument("--renderer-process-limit=1")   
        options.add_argument("--process-per-site")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
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
        
        if sys.platform.startswith("win"):
            service = Service(executable_path="../chromedriver.exe")
        elif sys.platform.startswith("linux"):
            service = Service(executable_path="../chromedriver")
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
                self.driver.set_page_load_timeout(30)  # limite para carregamento da página
                self.driver.get(url)

                try:
                    pre_element = WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "pre"))
                    )
                    json_text = pre_element.text
                    return json.loads(json_text)

                except Exception:
                    self.logger.warning("Elemento <pre> não encontrado (provável erro 403)")
                    raise PermissionError("Erro 403 detectado")

            except PermissionError:
                self.logger.warning(f"Erro 403 detectado. Reiniciando driver... Tentativa {tentativa}")
                self.restartDriver()
            except Exception as e:
                stacktrace = traceback.format_exc()
                self.logger.error(f"Erro inesperado na tentativa {tentativa}: {e}. Stacktrace: {stacktrace}")
                self.restartDriver()
        raise Exception(f"Falha ao obter JSON de {url} após {tentativas} tentativas")
    
    def stopDriver(self: Self):
        self.logger.info("Finalizando Driver")
        self.driver.quit()