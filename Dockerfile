# Imagem arm64-native (VM Oracle Ampere A1). Usa Chromium do Debian — não há
# Google Chrome oficial para ARM Linux.
FROM python:3.11.3-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LC_ALL=C.UTF-8 LANG=C.UTF-8 TZ=UTC

# Chromium headless + chromedriver (arm64-native) e libs necessárias.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium chromium-driver \
    fonts-liberation libasound2 libatk-bridge2.0-0 libnspr4 libnss3 \
    libx11-6 libx11-xcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 \
    libxkbcommon0 libxrandr2 libgbm1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Paths usados por SeleniumWebDriverService.
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copia o projeto
COPY src/ /app/src/

WORKDIR /app/src
ENTRYPOINT [ "python", "main.py" ]
