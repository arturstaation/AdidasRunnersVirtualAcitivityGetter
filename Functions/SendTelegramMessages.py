import telegram
import os

async def sendTelegramMessages(message):
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

    bot = telegram.Bot(token)
    async with bot:
        await bot.sendMessage(chat_id=chat_id, text=message)