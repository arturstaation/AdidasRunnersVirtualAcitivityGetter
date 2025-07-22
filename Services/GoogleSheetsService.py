import gspread
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.service_account import client
from datetime import datetime
from typing import Self
import os
import logging
import json
from gspread import Spreadsheet
from Models import AdidasCommunity
from datetime import datetime, timezone

class GoogleSheetsService:
    
    credentials: str
    sheetId: str
    credentials_dict: dict
    serviceAccount: client
    sheet : Spreadsheet

    def __init__(self: Self):
        self.credentials = os.getenv("GOOGLE_CREDENTIALS")
        self.sheetId = os.getenv("GOOGLE_SHEET_ID")
        self.credentials_dict = json.loads(self.credentials)
        self.serviceAccount = self.authenticate()
        self.getSheet()
        self.ensure_sheets_exist()
        self.remove_past_live_activities()

    def getSheet(self: Self):
        logging.info(f'Pegando Tabela de Id {self.sheetId}')
        self.sheet = self.serviceAccount.open_by_key(key=self.sheetId)
        print(self.sheet)

    def authenticate(self: Self) -> client:
        logging.info('Autenticando Conta de Serviço')
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials._from_parsed_json_keyfile(self.credentials_dict, scope)
        serviceAccount = gspread.authorize(creds)
        logging.info('Conta de Serviço Autenticada com sucesso')
        return serviceAccount

    def ensure_sheets_exist(self: Self):
        logging.info('Verifiando se as planilhas all_activities e live_activities existem')
        sheet_names = [ws.title for ws in self.sheet.worksheets()]
        logging.debug(f'Planilhas {sheet_names} encontradas')
        if "all_activities" not in sheet_names:
            logging.info(f'Planilha all_activities não foi encontrada. Seguindo com a criação')
            self.sheet.add_worksheet(title="all_activities", rows="1000", cols="10")
            self.sheet.worksheet("all_activities").append_row(["id", "name", "startDate", "community"])
            logging.info(f'Planilha all_activities criada')
        if "live_activities" not in sheet_names:
            logging.info(f'Planilha live_activities não foi encontrada. Seguindo com a criação')
            self.sheet.add_worksheet(title="live_activities", rows="1000", cols="10")
            self.sheet.worksheet("live_activities").append_row(["id", "name", "startDate", "community"])
            logging.info(f'Planilha live_activities criada')

    def remove_past_live_activities(self: Self):
        logging.info("Verificando Atividades Ja Existentes Na Planilha do GoogleSheets")
        live_ws = self.sheet.worksheet("live_activities")
        all_ws = self.sheet.worksheet("all_activities")

        rows = live_ws.get_all_values()
        if len(rows) <= 1:
            logging.info("Tabela live_activities vazia")
            return

        header = rows[0]
        data_rows = rows[1:]

        now = datetime.now()
        valid_rows = []
        expired_rows = []


        logging.info("Separando linhas da tabela live_activities em ativas e inativas")
        for row in data_rows:
            try:
                start_time = datetime.strptime(row[2], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
                
                if start_time > now:
                    valid_rows.append(row)
                else:
                    expired_rows.append(row)
            except Exception as e:
                logging.error(f"Erro ao converter data: {row[2]} - {e}. Pulando validação das datas para evitar erro catastrofico")
                return
                


        logging.info(f"Reescrevendo planilha live_activities com {len(valid_rows)} atividades")
        live_ws.clear()
        live_ws.append_rows([header] + valid_rows)

        if expired_rows:
            
            logging.info(f"Movendo {len(expired_rows)} Atividades expiradas para a planilha all_activities")
            all_ws.append_rows(expired_rows)


    def add_new_activities(self: Self, arCommunity: AdidasCommunity):
        if(len(arCommunity.events) == 0):
            logging.info(f"A Comunidade {arCommunity.name} não possui atividades")
            return
        logging.info(f"Verificando Atividades da Comunidade {arCommunity.name}")
        live_ws = self.sheet.worksheet("live_activities")
        existing_rows = live_ws.get_all_values()

        if len(existing_rows) == 0:
            logging.info("Tabela live_activities vazia, incluindo cabeçalho")
            raise ValueError("A aba 'live_activities' está vazia. Adicione um cabeçalho antes.")

        existing_ids = {str(row[0]) for row in existing_rows[1:]}
        new_rows = []
        new_events = []

        for event in arCommunity.events:
            if str(event.id) not in existing_ids:
                new_rows.append([event.id, event.name, event.startDate, arCommunity.name])
                new_events.append(event)

        logging.info(f"Foram Encontradas {len(new_events)} novos eventos para comunidade {arCommunity.name}")
        if new_rows:
            logging.info(f"Adicionando Novas Atividades da Comunidade {arCommunity.name} ao GoogleSheets")
            logging.debug(f"Atividades: {new_rows}")
            live_ws.append_rows(new_rows, value_input_option='RAW')

        arCommunity.setEvents(new_events)

