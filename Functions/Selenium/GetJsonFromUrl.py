from .GetDriver import getDriver
import json

def getJsonFromUrl(url : str) -> json:
    driver = getDriver()
    driver.get(url)

    json_text = driver.find_element("tag name", "pre").text

    data = json.loads(json_text)
    driver.quit()
    return data
