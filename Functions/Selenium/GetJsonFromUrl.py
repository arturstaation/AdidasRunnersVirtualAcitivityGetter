from .GetDriver import getDriver
import json
import logging

def getJsonFromUrl(url : str) -> json:
    driver = getDriver()

    logging.info(f"Acessando URL {url}")
    driver.get(url)

    logging.info(f"Extraindo dados URL {url}")
    json_text = driver.find_element("tag name", "pre").text

    logging.info(f"Convertendo dados da URL {url} em json")
    data = json.loads(json_text)
    driver.quit()
    return data
