from typing import List
from Functions import (getAdidasRunnersCommunity, getAdidasRunnersCommunityEvents, sendTelegramMessages)
from Models import (AdidasRunnersEvent, AdidasCommunity)
from dotenv import load_dotenv
import asyncio
from datetime import datetime


def salvar_atividades_em_txt(events: List[AdidasRunnersEvent], nome_arquivo: str = "atividades.txt"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        for event in events:
            linha = f"id: {event.id} | nome: {event.name} | comunidade: {event.community} |categoria: {event.category} | início: {event.startDate}\n"
            f.write(linha)

def gerar_mensagem_telegram(events: List[AdidasRunnersEvent], community: AdidasCommunity) -> str:
    mensagem = f"<b>📢 Novas atividades do Adidas Runners:</b>\n\n<b>{community.name}</b>\n\n"
    for event in events:
        mensagem += (
            f"<b>• Nome:</b> {event.name}\n"
            f"<b>• Categoria:</b> {event.category}\n"
            f"<b>• Início:</b> {format_date(event.startDate)}\n\n"
        )
    return mensagem


def format_date(data_iso: str) -> str:
    dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y às %H:%M")

def main():
    load_dotenv()

    arCommunityList = getAdidasRunnersCommunity()
    for arCommunity in arCommunityList:
        currentARCommunityEventsList = getAdidasRunnersCommunityEvents(arCommunity)
        salvar_atividades_em_txt(currentARCommunityEventsList)
        asyncio.run(sendTelegramMessages(gerar_mensagem_telegram(currentARCommunityEventsList, arCommunity)))
        break

if __name__ == '__main__':
    main()
