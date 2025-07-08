import logging
from Models import (AdidasRunnersEvent, AdidasCommunity)
from typing import List, Self
import telegram
import os
import logging
from .UtilsService import UtilsService

class TelegramService:

    utilsService : UtilsService

    def __init__(self: Self, utilsService: UtilsService):
        self.utilsService = utilsService 
        
        self.token = os.getenv("TOKEN")
        self.chat_id = os.getenv("CHAT_ID")

        self.bot = telegram.Bot(self.token)

    def generateMessage(self: Self, arCommunity: AdidasCommunity) -> str:
        logging.info("Formatando Mesangem")
        mensagem = f"<b>📢 Novas atividades do Adidas Runners:</b>\n\n<b>{arCommunity.name}</b>\n\n"
        for event in arCommunity.events:
            mensagem += (
                f"<b>• Nome:</b> {event.name}\n"
                f"<b>• Categoria:</b> {event.category}\n"
                f"<b>• Início:</b> {self.utilsService.formatDate(event.startDate)}\n\n"
            )
        return mensagem
    
    async def sendTelegramMessages(self:Self, message:str):
        async with self.bot:
            
            logging.info(f"Enviando Mesangem {message} Para o chat {self.chat_id}")
            await self.bot.sendMessage(chat_id=self.chat_id, text=message, parse_mode='HTML')