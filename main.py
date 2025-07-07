from typing import List
from Functions import (getAdidasRunnersCommunity, getAdidasRunnersCommunityEvents, sendTelegramMessages)
from Models import (AdidasRunnersEvent)
from dotenv import load_dotenv
import asyncio


def main():
    load_dotenv()

    def salvar_atividades_em_txt(events: List[AdidasRunnersEvent], nome_arquivo: str = "atividades.txt"):
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            for event in events:
                linha = f"id: {event.id} | nome: {event.name} | comunidade: {event.community} |categoria: {event.category} | início: {event.startDate}\n"
                f.write(linha)

    def gerar_mensagem_telegram(events: List[AdidasRunnersEvent]) -> str:
        mensagem = "*📢 Novas atividades do Adidas Runners:*\n\n"
        for event in events:
            mensagem += (
                f"*• Nome:* {event.name}\n"
                f"*• Comunidade:* {event.community}\n"
                f"*• Categoria:* {event.category}\n"
                f"*• Início:* {event.startDate}\n"
            )
        return mensagem

    arCommunityList = getAdidasRunnersCommunity()
    for arCommunity in arCommunityList:
        currentARCommunityEventsList = getAdidasRunnersCommunityEvents(arCommunity)
        salvar_atividades_em_txt(currentARCommunityEventsList)
        sendTelegramMessages(gerar_mensagem_telegram(currentARCommunityEventsList))
        break

if __name__ == '__main__':
    asyncio.run(main())
