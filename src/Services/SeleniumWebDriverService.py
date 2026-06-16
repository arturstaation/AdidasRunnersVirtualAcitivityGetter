from logging import Logger
from selenium import webdriver
from seleniumwire import webdriver as wire_webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import Self
from .UtilsService import UtilsService
from .ProxyService import ProxyService
import traceback
import os
from tempfile import mkdtemp

class SeleniumWebDriverService:

    driver : webdriver
    utilsService: UtilsService
    logger : Logger
    hasProxy: bool
    driver_path: str

    def __init__(self: Self, logger : Logger, utilsService: UtilsService):
        self.logger = logger
        self.logger.info("Inicializando SeleniumWebDriver")
        self.utilsService = utilsService
        self.hasProxy=self.utilsService.strToBool(os.getenv('PROXY_ENABLED', "False"))
        # Em ARM (VM Oracle) não há Google Chrome/chromedriver oficial; usamos o
        # chromium-driver do sistema via caminho fixo (arm64-native).
        self.driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        self.logger.info(f"Usando ChromeDriver em {self.driver_path}")
        self.getDriver()

    def getDriver(self: Self):
        self.logger.info("Criando Selenium WebDriver")
        options = Options()
        options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
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
        options.add_argument(f'--user-agent={os.getenv("AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")}')

        service = Service(self.driver_path)
        if(self.hasProxy):
            # Modo proxy: selenium-wire (MITM) + ProxyService. Mantido pronto, porém
            # hoje DESABILITADO (PROXY_ENABLED=false) — a VM acessa a Adidas direto
            # com Chromium real. Ao REATIVAR, pode ser preciso pinar o pyOpenSSL: o
            # selenium-wire quebra em versões novas (X509.get_extension removido).
            proxyService = ProxyService(self.logger)
            proxyService.getNewProxy()

            self.logger.info("Gerando Proxy")
            proxySettings = proxyService.getProxySettings()

            proxyUrl= f"http://{proxySettings.proxyUser}:{proxySettings.proxyPassword}@{proxySettings.proxyAddress}:{proxySettings.proxyPort}"

            seleniumwireOptions = {
                "proxy":{
                    "http": proxyUrl,
                    "https": proxyUrl
                }
            }
            self.driver = wire_webdriver.Chrome(service=service, options=options, seleniumwire_options=seleniumwireOptions)
        else:
            # Modo padrão (sem proxy): selenium puro, sem o MITM do selenium-wire.
            self.driver = webdriver.Chrome(service=service, options=options)

    def restartDriver(self: Self):
        self.logger.warning("Reiniciando WebDriver")
        try:
            self.stopDriver()
        except:
            pass
        self.getDriver()
    
    def getJsonFromUrl(self, url: str, tentativas: int = 3) -> dict:
        lastError = None
        for tentativa in range(1, tentativas + 1):
            try:
                self.logger.info(f"[{tentativa}/{tentativas}] Acessando URL: {url}")
                try:
                    self.driver.set_page_load_timeout(30) 
                    self.driver.get(url)
                except TimeoutException as e:
                    self.logger.warning(f"A pagina {url} não carregou a tempo")
                    lastError =  str(e)
                    raise TimeoutException("A pagina não carregou a tempo")

                try:
                    pre_element = WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "pre"))
                    )
                    json_text = pre_element.text
                    return json.loads(json_text)
                except TimeoutException as e:
                    self.logger.warning("Elemento <pre> não encontrado (provável erro 403)")
                    lastError =  str(e)
                    raise PermissionError("Erro 403 detectado")
                except Exception as e:
                    self.logger.warning(f"Erro desconhecido. Erro: {str(e)}")
                    lastError =  str(e)
                    raise Exception(f"Erro Desconhecido: str{e}")
                
            except Exception as e:
                stacktrace = traceback.format_exc()
                lastError =  str(e)
                self.logger.error(f"Erro na tentativa {tentativa}: {e}. Stacktrace: {stacktrace}")
                self.restartDriver()
        raise Exception(f"Falha ao obter JSON de {url} após {tentativas} tentativas. Erro: {lastError}")
    
    def stopDriver(self: Self):
        self.logger.info("Finalizando Driver")
        if(self.driver):
            self.driver.quit()