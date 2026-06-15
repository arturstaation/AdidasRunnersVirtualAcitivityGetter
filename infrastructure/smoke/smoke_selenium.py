#!/usr/bin/env python3
"""Smoke-test ISOLADO do maior risco da migração: Chromium headless em ARM.

Não toca em Postgres nem Telegram — só prova que o Chromium do sistema
(arm64-native) + Selenium conseguem abrir a API do Adidas Runners e extrair o
JSON. Espelha as MESMAS options do SeleniumWebDriverService.

Uso (dentro da imagem arm64):
    python smoke_selenium.py
Sai com código 0 em sucesso, !=0 em falha (bom para CI/healthcheck).
"""
import json
import os
import sys
from tempfile import mkdtemp

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = (
    "https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/"
    "connect/communities?limit=100&type=AdidasRunners"
)


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    default_agent = (
        "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    )
    options.add_argument(f"--user-agent={os.getenv('AGENT', default_agent)}")
    service = Service(os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    return webdriver.Chrome(service=service, options=options)


def main() -> int:
    print(f"CHROME_BIN={os.getenv('CHROME_BIN', '/usr/bin/chromium')}")
    print(f"CHROMEDRIVER_PATH={os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')}")
    driver = None
    try:
        driver = build_driver()
        print(f"Chrome/Chromium iniciado OK. Acessando API...\n  {URL}")
        driver.set_page_load_timeout(30)
        driver.get(URL)
        pre = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        data = json.loads(pre.text)
        communities = data["_embedded"]["communities"]
        print(f"\n✅ SUCESSO: {len(communities)} comunidades retornadas pela API.")
        for c in communities[:5]:
            print(f"   - {c['id']}: {c['name']}")
        return 0
    except Exception as e:
        print(f"\n❌ FALHA: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
