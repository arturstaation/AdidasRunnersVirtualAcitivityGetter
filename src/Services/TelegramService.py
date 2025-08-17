from logging import Logger
from Models import (AdidasCommunity)
from typing import List, Self
import telegram
import os
import html
from .UtilsService import UtilsService
from uuid import UUID

class TelegramService:

    utilsService : UtilsService
    logger : Logger
    def __init__(self: Self, logger : Logger, utilsService: UtilsService):
        self.utilsService = utilsService 
        self.logger = logger
        self.token = os.getenv("TOKEN")
        self.chatId = os.getenv("CHAT_ID")
        self.adminChatId = os.getenv("ADMIN_CHAT_ID")
        print(self.token)
        self.bot = telegram.Bot(self.token)

    def generateMessage(self: Self, arCommunity: AdidasCommunity, messages: List[str]) -> str:
        self.logger.info(f"Formatando Atividades da {arCommunity.name} em mensagem")
        if(len(messages) == 0):
            message = f"<b>📢 Novas atividades do Adidas Runners:</b>\n\n<b>{arCommunity.name}</b>\n\n"
        else:
            message = f"<b>{arCommunity.name}</b>\n\n"
        for event in arCommunity.events:
            message += (
                f"<b>• Nome:</b> {event.name}\n"
                f"<b>• Categoria:</b> {event.category}\n"
                f"<b>• Início:</b> {self.utilsService.formatDate(event.startDate)}\n"
                f'<a href="https://www.adidas.com.br/adidasrunners/events/event/{event.id}">Ver evento</a>\n\n'
            )
        if(len(messages) == 0):
            self.logger.info(f"Primeira mensagem da fila do processamento atual")
            messages.append(message)
        elif(len(messages[len(messages)-1]) + len(message) > 4096):
            self.logger.info(f"Limite de caracteres da mensagem {len(message)+1} excedida, criando nova mensagem")
            messages.append(message)
        else:
            self.logger.info(f"Limite de caracteres da mensagem {len(message)+1} não excedida, adicionando conteudo")
            messages[-1] += message
        return messages
    
    async def sendTelegramMessages(self:Self, messages : List[str]):
        async with self.bot:
            
            for index, message in enumerate(messages): 
                self.logger.info(f"Enviando Mensagem {index+1}/{len(messages)}")
                self.logger.info(f"Enviando Mensagem {message} Para o chat {self.chatId}")
                await self.bot.sendMessage(chat_id=self.chatId, text=message, parse_mode='HTML')
    
    async def sendTelegramAdminMessage(self:Self, message: str):
        async with self.bot:
            self.logger.info(f"Enviando Mensagem ao Administrador")
            self.logger.info(f"Enviando Mensagem {message} Para o chat {self.adminChatId}")
            await self.bot.sendMessage(chat_id=self.adminChatId, text=message, parse_mode='HTML')

    def generateAdminErrorMessage(self: Self, processingId: UUID, err: Exception, stacktrace: str) -> str:
        self.logger.info("Formatando mensagem de erro para enviar ao administrador")
        
        pid = html.escape(str(processingId))
        err_text = html.escape(str(err)) if err is not None else ""
        st_text = html.escape(stacktrace or "")
        if len(err_text) > 800:
            err_text = err_text[:800] + "\n...[truncated]"
        if len(st_text) > 3500:
            st_text = st_text[:3500] + "\n...[truncated]"

        message = ""
        message += f"<b>❌ Erro de processamento</b>\n\n"
        message += f"<b>• Processing ID:</b> <code>{pid}</code>\n"
        message += f"<b>• Erro:</b>\n<pre>{err_text}</pre>\n"
        message += f"<b>• Stacktrace:</b>\n<pre>{st_text}</pre>"
        return message
    
    def generateAdminSuccessMessage(self: Self, processingId: UUID, empty: bool) -> str:
        self.logger.info("Formatando mensagem de processamento vazio")
        
        pid = html.escape(str(processingId))

        message = ""
        message += f"<b>✅ Processamento Finalizado com Sucesso</b>\n\n"
        message += f"<b>• Processing ID:</b> <code>{pid}</code>\n"
        if(empty):
            message += f"<b> O Processamento não encontrou nenhuma nova atividade</b>\n"
        return message