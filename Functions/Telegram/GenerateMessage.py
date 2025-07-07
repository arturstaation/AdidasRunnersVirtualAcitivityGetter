from Models import (AdidasRunnersEvent, AdidasCommunity)
from typing import List
from ..Utils.FormatDate import formatDate
import logging

def generateMessage(events: List[AdidasRunnersEvent], community: AdidasCommunity) -> str:
    logging.info("Formatando Mesangem")
    mensagem = f"<b>📢 Novas atividades do Adidas Runners:</b>\n\n<b>{community.name}</b>\n\n"
    for event in events:
        mensagem += (
            f"<b>• Nome:</b> {event.name}\n"
            f"<b>• Categoria:</b> {event.category}\n"
            f"<b>• Início:</b> {formatDate(event.startDate)}\n\n"
        )
    return mensagem