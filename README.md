# 🏃‍♂️ Adidas Runners Notifier Bot

## Objetivo do Projeto
Este projeto tem como objetivo monitorar e **enviar atualizações sobre eventos da comunidade Adidas Runners** diretamente para o seu Telegram via bot.

---

## 📦 Estrutura do Projeto

```text
adidas-runners-bot/
├── Services/                          # Diretório principal dos serviços
│   ├── __init__.py
│   ├── AdidasService.py              # Lida com dados da Adidas (comunidades e eventos)
│   ├── GoogleSheetsService.py       # Lida com as planilhas, gerenciando eventos ativos e inativos
│   ├── LoggerService.py             # Configuração do logging
│   ├── SeleniumWebDriverService.py  # Web scraping via Selenium
│   ├── TelegramService.py           # Envia mensagens, gera texto, etc
│   └── UtilsService.py              # Funções auxiliares como formatação de data
│
├── Models/                           # Classes de tipagem / entidades
│   ├── __init__.py
│   ├── adidasCommunityModel.py
│   └── adidasRunnersEventModel.py
│
├── main.py                           # Ponto de entrada da aplicação
├── .env                              # Variáveis de ambiente
├── application.log                   # Logs das execuções da aplicação
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ✅ Como Rodar o Projeto Localmente

### 1. 🔗 Clone o repositório

```bash
git clone https://github.com/seu-usuario/adidas-runners-bot.git
cd adidas-runners-bot
```

### 2. 📄 Crie o arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env` com o seguinte conteúdo:

```env
TOKEN=seu_token_aqui
CHAT_ID=seu_chat_id_aqui
ADMIN_CHAT_ID=seu_admin_chat_id_aqui
PROXY_USER=seu_proxy_user_aqui
PROXY_PASSWORD=seu_proxy_password_aqui
GOOGLE_CREDENTIALS=sua_google_credentials_aqui
GOOGLE_SHEET_ID=sua_google_sheet_id
```

- `TOKEN`: o token do seu bot do Telegram.  
- `CHAT_ID`: o ID do chat para onde o bot enviará as mensagens.
- `ADMIN_CHAT_ID`: o ID do chat para onde o bot enviará as mensagens de cunho administrativo.
- `PROXY_USER`: Usuario do Proxy DataImpulse
- `PROXY_PASSWORD`:  Senha do Usuario Proxy DataImpulse
- `GOOGLE_CREDENTIALS`: Credenciais da conta de serviço gerado para manipular as planilhas
- `GOOGLE_SHEET_ID`: Id da Planilha no GoogleDocs


📌 Para aprender a obter essas informações, siga este tutorial:  
🎥 [Como criar um bot no Telegram e pegar o TOKEN/CHAT_ID](https://www.youtube.com/watch?v=uGaJVTPBpkM)

### 3. ⚙️ Instalar Dependências

Instale os pacotes necessários com:

```bash
pip install -r requirements.txt
```
### 4. 🚀 Executando o Bot

```bash
python main.py
```
---
