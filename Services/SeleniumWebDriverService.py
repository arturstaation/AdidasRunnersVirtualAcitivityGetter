import logging
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from selenium.common.exceptions import NoSuchElementException
from typing import Self
from .UtilsService import UtilsService
from .ProxyService import ProxyService
from Models import ProxyModel

import time

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
        manifest_json, background_js = self.getExtensionData(proxyService.getProxySettings())
        pluginfile = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        options.add_extension(pluginfile)

        self.driver = webdriver.Chrome(options=options)

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
                time.sleep(2)

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

    @staticmethod
    def getExtensionData(proxyModel : ProxyModel):
        return """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """, """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxyModel.proxyAddress, proxyModel.proxyPort, proxyModel.proxyUser, proxyModel.proxyPassword)