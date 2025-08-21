# 🏃‍♂️ Adidas Runners Notifier Bot

## Objetivo do Projeto
Este projeto tem como objetivo monitorar e **enviar atualizações sobre eventos da comunidade Adidas Runners** diretamente para o seu Telegram via bot.

---

## 📦 Estrutura do Projeto

```text
adidas-runners-bot/
├── .github/                               # Configurações específicas para GitHub
│   └── workflows/                         # Onde ficam os workflows de CI/CD do GitHub Actions
│       └── python-app.yml                 # Workflow principal
│    
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
├── .coveragearc                           # Configurações relacionadas ao relatorio de cobertura dos testes
├── .env                                   # Variáveis de ambiente
├── application.log                        # Logs das execuções da aplicação
├── .gitignore                             # Define arquivos e pastas que não devem ser versionados no Git
├── chromedriver                           # Binário do ChromeDriver (Linux) para automação com Selenium
├── chromedriver.exe                       # Binário do ChromeDriver (Windows) para automação com Selenium
├── Dockerfile                             # Instruções para construir a imagem Docker da aplicação
├── requirements.txt                       # Lista de dependências Python necessárias para rodar o projeto
└── README.md                              # Documentação principal do repositório
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

---

## 🐳 Dockerfile

Este projeto utiliza um **Dockerfile** otimizado para rodar em **AWS Lambda** com suporte a **Google Chrome Headless + Selenium**.

### 🔎 O que ele faz

1. **Base da imagem**

   * Usa `python:3.11.3-slim` (imagem leve com Python 3.11.3).
   * Configura variáveis de ambiente para evitar cache de bytecode, manter logs em tempo real e definir locale.

2. **Instala dependências do sistema**

   * Pacotes necessários para rodar o **Google Chrome** em modo headless (bibliotecas gráficas mínimas, fontes, utilitários como `curl` e `unzip`).

3. **Instala Google Chrome (stable)**

   * Adiciona o repositório oficial do Chrome.
   * Instala a versão estável do navegador.
   * Define `CHROME_BIN=/usr/bin/google-chrome` para que o Selenium consiga localizar o binário.

4. **Instala dependências Python**

   * Copia o `requirements.txt`.
   * Atualiza `pip` e `wheel`.
   * Instala as dependências do projeto.
   * Instala `awslambdaric`, runtime necessário para executar a aplicação no **AWS Lambda**.

5. **Copia o código do projeto**

   * Copia a pasta `src/` para `/app/src`.
   * Copia o `chromedriver` (da raiz do projeto) para `/app/`.
   * Dá permissão de execução no `chromedriver`.
   * Define `CHROMEDRIVER=/app/chromedriver` como variável de ambiente.

6. **Define o ponto de entrada**

   * `ENTRYPOINT [ "python", "-m", "awslambdaric" ]` → inicializa o runtime da AWS Lambda.
   * `CMD ["main.lambda_handler"]` → define a função handler que será chamada pela Lambda.

---

### ▶️ Como usar localmente

Construir a imagem:

```bash
docker build -t adidasrunnersbot .
```

Rodar a imagem simulando Lambda:

```bash
docker run --rm adidasrunnersbot
```

## 🔄 Github Actions

Este repositório utiliza GitHub Actions para automatizar o processo de testes, build de imagens Docker, deploy na AWS Lambda via ECR e envio de relatórios por e-mail.

O workflow está definido em .github/workflows/python-app.yml.

### Fluxo dos Jobs

1. **`build`**

   * Ambiente: `ubuntu-latest`
   * Instala o **Python 3.11.3**.
   * Instala as dependências do projeto (`requirements.txt`).
   * Executa os testes com **pytest**.
   * Gera relatório de cobertura em XML (`src/coverage.xml`).
   * Publica o relatório de cobertura como artifact no GitHub Actions.
   * Mostra resumo da cobertura no **Job Summary**.

2. **`deploy_aws`**

   * Depende do job `build`.
   * Faz login na AWS usando **GitHub Secrets**.
   * Faz login no **Amazon ECR**.
   * Constrói e publica a imagem Docker no repositório **ECR** `adidasrunners`.
   * Atualiza a função **AWS Lambda** `adidasrunnersbot` para usar a nova imagem.

3. **`send_email`**

   * Sempre roda (`if: always()`), independente de falhas nos jobs anteriores.
   * Monta um resumo do status de todos os jobs (`success`, `failure` ou `skipped`).
   * Envia um e-mail de notificação com:

     * Resultado por job.
     * Branch, commit e autor.
     * Link para o run no GitHub Actions.

---

### ⚙️ Configuração Necessária

Antes de usar o workflow, você precisa configurar **GitHub Secrets** com credenciais de Docker, AWS e SMTP.

#### 🔑 Secrets obrigatórios

* **AWS**
  * `AWS_ACCESS_KEY_ID`
  * `AWS_SECRET_ACCESS_KEY`

-----
* **SMTP (para envio de e-mail)**
  * `SMTP_SERVER` → servidor SMTP
  * `SMTP_PORT` → porta SMTP (ex: `587`)
  * `SMTP_USERNAME` → usuário da conta de e-mail
  * `SMTP_PASSWORD` → senha ou token do e-mail
  * `EMAIL_FROM` → remetente
  * `EMAIL_TO` → destinatário(s)

#### Como configurar SMTP (Exemplo com Gmail)

##### 1. Pré-requisitos (exemplo com Gmail)

* Ative a **Verificação em 2 Etapas** na sua conta Google.
* Gere uma **App Password**.
* Utilize essa **App Password** como `SMTP_PASSWORD` no GitHub Secrets.

##### 2. (Gmail) Coletar configurações SMTP

* **Servidor SMTP:** `smtp.gmail.com`
* **Porta SSL (implícito):** `465`
* **Porta TLS/STARTTLS:** `587`

##### 3. Criar **Secrets** no GitHub

Vá até **Settings → Secrets and variables → Actions → New repository secret** e crie:

| Nome do Secret  | Valor exato a usar                                 |
| --------------- | -------------------------------------------------- |
| `SMTP_SERVER`   | `smtp.gmail.com`                                   |
| `SMTP_PORT`     | `587` (para TLS) ou `465` (para SSL)               |
| `SMTP_USERNAME` | Seu e-mail (ex.: `seuusuario@gmail.com`)           |
| `SMTP_PASSWORD` | App Password gerada (não use senha normal)         |
| `EMAIL_FROM`    | Remetente (ex.: `adidasrunnersbot@seudominio.com`) |
| `EMAIL_TO`      | Destinatário(s), separados por vírgula             |

> ℹ️ Se estiver usando outro provedor (Outlook, Yahoo, etc.), substitua os valores de `SMTP_SERVER`, `SMTP_PORT` e `SMTP_USERNAME` pelas credenciais do seu serviço de e-mail.

> ℹ️ Qualquer dúvida, siga o tutorial do vídeo: [https://www.youtube.com/watch?v=FFm1to\_vIDc](https://www.youtube.com/watch?v=FFm1to_vIDc)

---

### ▶️ Como rodar

O workflow é acionado automaticamente em:

* **push** para a branch `main`
* **pull request** na branch `main`
* **manual** via **workflow\_dispatch** no GitHub Actions

---