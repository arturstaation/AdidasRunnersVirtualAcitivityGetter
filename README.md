# 🏃‍♂️ Adidas Runners Notifier Bot

Este projeto tem como objetivo monitorar e **enviar atualizações sobre eventos da comunidade Adidas Runners** diretamente para o seu Telegram via bot.

---

## ✅ Como Rodar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/adidas-runners-bot.git
cd adidas-runners-bot
```

### 2. Crie o arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env` com o seguinte conteúdo:

```env
TOKEN=seu_token_aqui
CHAT_ID=seu_chat_id_aqui
```

- `TOKEN`: o token do seu bot do Telegram.  
- `CHAT_ID`: o ID do chat para onde o bot enviará as mensagens.

📌 Para aprender a obter essas informações, siga este tutorial:  
🎥 [Como criar um bot no Telegram e pegar o TOKEN/CHAT_ID](https://www.youtube.com/watch?v=uGaJVTPBpkM)

---

## ⚙️ Dependências

Instale os pacotes necessários com:

```bash
pip install -r requirements.txt
```

---

## 🚀 Executando o Bot

Após configurar o `.env`, basta rodar:

```bash
python main.py
```

O bot irá buscar eventos da comunidade Adidas Runners e enviar atualizações diretamente para o Telegram.

---

## 📦 Estrutura do Projeto

```text
adidas-runners-bot/
├── Functions/
│   ├── __init__.py
│   ├── GetAdidasRunnersCommunity.py
│   ├── GetAdidasRunnersCommunityEvents.py
│   ├── GetDriver.py
│   ├── GetJsonFromUrl.py
│   └── SendTelegramMessages.py
├── Models/
│   ├── __init__.py
│   ├── adidasCommunityModel.py
│   └── adidasRunnersEventModel.py
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---
