import telegram
import os
import logging

async def sendTelegramMessages(message:str):
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")

    bot = telegram.Bot(token)
    async with bot:
        
        logging.info(f"Enviando Mesangem {message} Para o chat {chat_id}")
        await bot.sendMessage(chat_id=chat_id, text=message, parse_mode='HTML')