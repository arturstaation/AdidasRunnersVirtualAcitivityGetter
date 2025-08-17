# 🏃‍♂️ Adidas Runners Notifier Bot

## Objetivo do Projeto
Este projeto tem como objetivo monitorar e **enviar atualizações sobre eventos da comunidade Adidas Runners** diretamente para o seu Telegram via bot.

---

## 📦 Estrutura do Projeto

```text
adidas-runners-bot/
├── src/
│   ├── Services/                          # Diretório principal dos serviços
│   │   ├── __init__.py
│   │   ├── AdidasService.py              # Lida com dados da Adidas (comunidades e eventos)
│   │   ├── GoogleSheetsService.py       # Lida com as planilhas, gerenciando eventos ativos e inativos
│   │   ├── LoggerService.py             # Configuração do logging
│   │   ├── SeleniumWebDriverService.py  # Web scraping via Selenium
│   │   ├── TelegramService.py           # Envia mensagens, gera texto, etc
│   │   └── UtilsService.py              # Funções auxiliares como formatação de data
│   │
│   ├── Models/                           # Classes de tipagem / entidades
│   │   ├── __init__.py
│   │   ├── adidasCommunityModel.py
│   │   └── adidasRunnersEventModel.py
│   │
│   └── main.py                           # Ponto de entrada da aplicação
│
├── Testes/                                # Testes unitários espelhando a estrutura da src
│   ├── Services/                          # Diretório principal dos serviços (testes)
│   │   ├── __init__.py
│   │   ├── test_AdidasService.py         # Testes para dados da Adidas (comunidades e eventos)
│   │   ├── test_GoogleSheetsService.py   # Testes para planilhas, eventos ativos e inativos
│   │   ├── test_LoggerService.py         # Testes da configuração do logging
│   │   ├── test_SeleniumWebDriverService.py  # Testes de web scraping via Selenium
│   │   ├── test_TelegramService.py       # Testes de envio de mensagens, geração de texto, etc
│   │   └── test_UtilsService.py          # Testes das funções auxiliares como formatação de data
│   │
│   ├── Models/                           # Testes das classes de tipagem / entidades
│   │   ├── __init__.py
│   │   ├── test_adidasCommunityModel.py
│   │   └── test_adidasRunnersEventModel.py
│   │
│   └── test_main.py                       # Testes do ponto de entrada da aplicação
│
├── .env                                   # Variáveis de ambiente
├── application.log                        # Logs das execuções da aplicação
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ✅ Como Rodar o Projeto Localmente

### 1. 🔗 Clone o repositório

```bash
git clone https://github.com/seu-usuario/adidas-runners-bot.git
cd adidas-runners-bot/src
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

## Como rodar os testes unitários

Antes de começar, garanta que as dependências de desenvolvimento estão instaladas (por exemplo, pytest e pytest-cov). Se estiver usando pip, você pode instalar com:
```bash
pip install -r requirements.txt
```

Defina a variável de ambiente PYTHONPATH apontando para a pasta src para que os imports funcionem corretamente.

No PowerShell (Windows):
```powershell
$env:PYTHONPATH = "src/"
```

No Bash (Linux/macOS):
```bash
export PYTHONPATH="src/"
```

Para executar todos os testes:
```bash
pytest Testes
```

Para executar um teste específico (exemplo: arquivo ou teste pontual):
```bash
# Por arquivo
pytest Testes/test_exemplo.py

# Por nome de teste (substring do nome)
pytest -k "nome_do_teste"
```

Para ver logs/saída de print durante os testes:
```bash
pytest -s
```

Para obter um relatório de cobertura:
```bash
pytest -q Testes --cov=src/ --cov-branch --cov-report=term-missing --cov-report=xml:src/coverage.xml
```

Isso irá calcular a cobertura de código do diretório src (incluindo verificação por branch), exibir no terminal as linhas não cobertas (term-missing), gerar um arquivo XML em src/coverage.xml (útil para CI).
```