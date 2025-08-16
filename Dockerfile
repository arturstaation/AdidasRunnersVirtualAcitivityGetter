# Usa Linux + Python 3.11.3
FROM python:3.11.3-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC

# Dependências do Chrome headless e utilitários básicos
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates unzip \
    fonts-liberation libasound2 libatk-bridge2.0-0 libnspr4 libnss3 \
    libx11-6 libx11-xcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 \
    libxkbcommon0 libxrandr2 libgbm1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Instala Google Chrome (stable)
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Paths úteis
ENV CHROME_BIN=/usr/bin/google-chrome \
    CHROMEDRIVER=/usr/local/bin/chromedriver

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copia o projeto (inclui seu chromedriver da raiz)
COPY . .

# Move seu chromedriver para o PATH e garante permissão de execução
# Se o arquivo não se chamar exatamente 'chromedriver', ajuste abaixo.
RUN if [ -f "/app/chromedriver-linux64/chromedriver" ]; then \
        mv /app/chromedriver /usr/local/bin/chromedriver && chmod +x /usr/local/bin/chromedriver; \
    elif [ -f "/app/chromedriver.exe" ]; then \
        mv /app/chromedriver.exe /usr/local/bin/chromedriver && chmod +x /usr/local/bin/chromedriver; \
    fi

# Executa seu app
CMD ["python", "main.py"]