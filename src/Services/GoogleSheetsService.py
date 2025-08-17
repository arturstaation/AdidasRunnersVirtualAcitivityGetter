import gspread
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.service_account import client
from datetime import datetime
from typing import Self
from gspread import Spreadsheet
from Models import AdidasCommunity
from datetime import datetime, timezone
from logging import Logger
import os
import json
import traceback

class GoogleSheetsService:
    
    credentials: str
    sheetId: str
    credentials_dict: dict
    serviceAccount: client
    sheet : Spreadsheet
    logger: Logger

    def __init__(self: Self, logger : Logger):
        self.logger = logger
        self.credentials = os.getenv("GOOGLE_CREDENTIALS")
        self.sheetId = os.getenv("GOOGLE_SHEET_ID")
        self.credentials_dict = json.loads(self.credentials)
        self.serviceAccount = self.authenticate()
        self.getSheet()
        self.ensureSheetsExist()
        self.removePastLiveActivities()

    def getSheet(self: Self):
        self.logger.info(f'Pegando Tabela de Id {self.sheetId}')
        self.sheet = self.serviceAccount.open_by_key(key=self.sheetId)

    def authenticate(self: Self) -> client:
        self.logger.info('Autenticando Conta de Serviço')
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials._from_parsed_json_keyfile(self.credentials_dict, scope)
        serviceAccount = gspread.authorize(creds)
        self.logger.info('Conta de Serviço Autenticada com sucesso')
        return serviceAccount

    def ensureSheetsExist(self: Self):
        self.logger.info('Verifiando se as planilhas expired_activities e live_activities existem')
        sheet_names = [ws.title for ws in self.sheet.worksheets()]
        self.logger.debug(f'Planilhas {sheet_names} encontradas')
        if "expired_activities" not in sheet_names:
            self.logger.info(f'Planilha expired_activities não foi encontrada. Seguindo com a criação')
            self.sheet.add_worksheet(title="expired_activities", rows="1000", cols="10")
            self.sheet.worksheet("expired_activities").append_row(["id", "name", "startDate", "community"])
            self.logger.info(f'Planilha expired_activities criada')
        if "live_activities" not in sheet_names:
            self.logger.info(f'Planilha live_activities não foi encontrada. Seguindo com a criação')
            self.sheet.add_worksheet(title="live_activities", rows="1000", cols="10")
            self.sheet.worksheet("live_activities").append_row(["id", "name", "startDate", "community"])
            self.logger.info(f'Planilha live_activities criada')

    def removePastLiveActivities(self: Self):
        self.logger.info("Verificando Atividades na planilha")
        live_ws = self.sheet.worksheet("live_activities")
        expired_ws = self.sheet.worksheet("expired_activities")

        rows = live_ws.get_all_values()
        if len(rows) <= 1:
            self.logger.info("Tabela live_activities vazia")
            return

        header = rows[0]
        data_rows = rows[1:]

        now = datetime.now(timezone.utc)

        valid_rows = []
        expired_rows = []

        self.logger.info("Separando linhas da tabela live_activities em ativas e expiradas")
        for row in data_rows:
            try:
                start_time = datetime.strptime(row[2], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
                if start_time > now:
                    valid_rows.append(row)
                else:
                    expired_rows.append(row)
            except Exception as e:
                stacktrace = traceback.format_exc()
                self.logger.error(
                    f"Erro ao converter data: {row[2]} - {e}. "
                    f"Pulando linha. Stacktrace: {stacktrace}"
                )
                continue

        if not expired_rows:
            self.logger.info("Nenhuma atividade expirada encontrada")
            return
        
        self.logger.info(f"Atualizando live_activities: mantendo {len(valid_rows)} e removendo {len(expired_rows)} expiradas")
        live_ws.clear()
        live_ws.append_rows([header] + valid_rows, value_input_option="RAW")

        try:
            self.logger.info(f"Adicionando {len(expired_rows)} linhas em expired")
            expired_ws.append_rows(expired_rows, value_input_option="RAW")
        except Exception as e:
            self.logger.warning(f"Falha ao anexar em expired: {e}")
            self.logger.info("Verificando Atividades Ja Existentes Na Planilha do GoogleSheets")
            live_ws = self.sheet.worksheet("live_activities")
            all_ws = self.sheet.worksheet("expired_activities")

            rows = live_ws.get_all_values()
            if len(rows) <= 1:
                self.logger.info("Tabela live_activities vazia")
                return

            header = rows[0]
            data_rows = rows[1:]

            now = datetime.now()
            valid_rows = []
            expired_rows = []


            self.logger.info("Separando linhas da tabela live_activities em ativas e inativas")
            for row in data_rows:
                try:
                    start_time = datetime.strptime(row[2], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
                    
                    if start_time > now:
                        valid_rows.append(row)
                    else:
                        expired_rows.append(row)
                except Exception as e:
                    stacktrace = traceback.format_exc()
                    self.logger.error(f"Erro ao converter data: {row[2]} - {e}. Pulando validação das datas para evitar erro catastrofico. Stacktrace: {stacktrace}")
                    return
                    


            self.logger.info(f"Reescrevendo planilha live_activities com {len(valid_rows)} atividades")
            live_ws.clear()
            live_ws.append_rows([header] + valid_rows)

            if expired_rows:
                
                self.logger.info(f"Movendo {len(expired_rows)} Atividades expiradas para a planilha expired_activities")
                all_ws.append_rows(expired_rows)


    def addNewActivities(self: Self, arCommunity: AdidasCommunity):
        if(len(arCommunity.events) == 0):
            self.logger.info(f"A Comunidade {arCommunity.name} não possui atividades")
            return
        self.logger.info(f"Verificando Atividades da Comunidade {arCommunity.name}")
        live_ws = self.sheet.worksheet("live_activities")
        existing_rows = live_ws.get_all_values()

        if len(existing_rows) == 0:
            self.logger.info("Tabela live_activities vazia, incluindo cabeçalho")
            raise ValueError("A aba 'live_activities' está vazia. Adicione um cabeçalho antes.")

        existing_ids = {str(row[0]) for row in existing_rows[1:]}
        new_rows = []
        new_events = []
        now = datetime.now(timezone.utc)
        for event in arCommunity.events:
            start_time = datetime.strptime(event.startDate, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            if str(event.id) not in existing_ids and start_time > now:
                new_rows.append([event.id, event.name, event.startDate, arCommunity.name])
                new_events.append(event)

        self.logger.info(f"Foram Encontradas {len(new_events)} novos eventos para comunidade {arCommunity.name}")
        if new_rows:
            self.logger.info(f"Adicionando Novas Atividades da Comunidade {arCommunity.name} ao GoogleSheets")
            self.logger.debug(f"Atividades: {new_rows}")
            live_ws.append_rows(new_rows, value_input_option='RAW')

        arCommunity.setEvents(new_events)

