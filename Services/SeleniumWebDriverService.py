import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from typing import Self

class SeleniumWebDriverService:

    driver : webdriver

    def __init__(self: Self):
        logging.info("Inicializando SeleniumWebDriver")
        self.getDriver()

    def getDriver(self: Self):
        logging.info("Criando Selenium WebDriver")
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(options=options)

    def getJsonFromUrl(self: Self, url : str) -> json:
        
        logging.info(f"Acessando URL {url}")
        self.driver.get(url)

        logging.info(f"Extraindo dados URL {url}")
        json_text = self.driver.find_element("tag name", "pre").text

        logging.info(f"Convertendo dados da URL {url} em json")
        data = json.loads(json_text)
        return data
    
    def stopDriver(self: Self):
        self.driver.quit()