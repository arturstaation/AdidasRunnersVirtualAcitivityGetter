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

    def generateMessage(self: Self, arCommunity: AdidasCommunity, messages: List[str]) -> str:
        logging.info("Formatando Mesangem")
        message = f"<b>📢 Novas atividades do Adidas Runners:</b>\n\n<b>{arCommunity.name}</b>\n\n"
        for event in arCommunity.events:
            message += (
                f"<b>• Nome:</b> {event.name}\n"
                f"<b>• Categoria:</b> {event.category}\n"
                f"<b>• Início:</b> {self.utilsService.formatDate(event.startDate)}\n"
                f'<a href="https://www.adidas.com.br/adidasrunners/events/event/{event.id}">Ver evento</a>\n\n'
            )
        if(len(messages) == 0):
            messages.append(message)
        elif(len(messages[len(messages)-1]) + len(message) > 4096):
            messages.append(message)
        return messages
    
    async def sendTelegramMessages(self:Self, messages : List[str]):
        async with self.bot:
            
            for index, message in enumerate(messages): 
                logging.info(f"Enviando Mensagem {index+1}/{len(messages)}")
                logging.info(f"Enviando Mensagem {message} Para o chat {self.chat_id}")
                await self.bot.sendMessage(chat_id=self.chat_id, text=message, parse_mode='HTML')