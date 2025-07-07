from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging

def getDriver():
    logging.info("Criando Selenium WebDriver")
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=options)
    return driver