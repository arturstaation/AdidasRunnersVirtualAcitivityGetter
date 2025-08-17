import json
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest

from Services.GoogleSheetsService import GoogleSheetsService


# --------------- Helpers ---------------

def _iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _setup_sheet_with_tabs(fake_sa):
    """Cria um sheet com abas live_activities e expired_activities mockadas e
    conecta em fake_sa.open_by_key."""
    live_ws = MagicMock()
    expired_ws = MagicMock()
    live_ws.title = "live_activities"
    expired_ws.title = "expired_activities"

    sheet = MagicMock()
    sheet.worksheets.return_value = [live_ws, expired_ws]

    def _get_ws(name):
        if name == "live_activities":
            return live_ws
        if name == "expired_activities":
            return expired_ws
        raise Exception("worksheet não esperada: " + name)

    sheet.worksheet.side_effect = _get_ws
    fake_sa.open_by_key.return_value = sheet
    return sheet, live_ws, expired_ws


# --------------- Fixtures ---------------

@pytest.fixture(autouse=True)
def _env(monkeypatch):
    fake_creds = {"type": "service_account", "project_id": "fake"}
    monkeypatch.setenv("GOOGLE_CREDENTIALS", json.dumps(fake_creds))
    monkeypatch.setenv("GOOGLE_SHEET_ID", "fake-sheet-id")
    yield
    monkeypatch.delenv("GOOGLE_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SHEET_ID", raising=False)


@pytest.fixture
def logger():
    lg = logging.getLogger("GoogleSheetsServiceTest")
    lg.setLevel(logging.INFO)
    return lg


# --------------- Testes de init/autenticação ---------------

@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_init_auth_and_open_sheet(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    fake_sheet = MagicMock()
    fake_sa.open_by_key.return_value = fake_sheet

    with caplog.at_level(logging.INFO):
        # Evita que __init__ rode a limpeza de atividades ao criar a instância
        with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
            svc = GoogleSheetsService(logger=logger)

    fake_sa.open_by_key.assert_called_once_with(key="fake-sheet-id")
    assert any("Autenticando Conta de Serviço" in m for m in caplog.messages)
    assert any("Pegando Tabela de Id fake-sheet-id" in m for m in caplog.messages)


# --------------- Testes de ensureSheetsExist ---------------

@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_ensureSheetsExist_creates_when_missing(p_keyfile, p_authorize, logger):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa

    # sheet sem as abas
    sheet = MagicMock()
    sheet.worksheets.return_value = []

    created_expired = MagicMock()
    created_live = MagicMock()

    def add_worksheet(title, rows, cols):
        ws = MagicMock()
        ws.title = title
        return ws

    sheet.add_worksheet.side_effect = add_worksheet

    def _worksheet(name):
        if name == "expired_activities":
            return created_expired
        if name == "live_activities":
            return created_live
        raise Exception("worksheet não esperada")

    sheet.worksheet.side_effect = _worksheet
    fake_sa.open_by_key.return_value = sheet

    # Evita que ensureSheetsExist rode dentro do __init__ para não duplicar chamadas
    with patch("Services.GoogleSheetsService.GoogleSheetsService.ensureSheetsExist", lambda self: None), \
         patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    # Agora testamos o método real, uma única execução
    GoogleSheetsService.ensureSheetsExist(svc)

    assert sheet.add_worksheet.call_count == 2
    created_expired.append_row.assert_called_once_with(["id", "name", "startDate", "community"])
    created_live.append_row.assert_called_once_with(["id", "name", "startDate", "community"])


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_ensureSheetsExist_noop_when_present(p_keyfile, p_authorize, logger):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa

    sheet = MagicMock()
    live_ws = MagicMock()
    expired_ws = MagicMock()
    live_ws.title = "live_activities"
    expired_ws.title = "expired_activities"
    sheet.worksheets.return_value = [live_ws, expired_ws]
    sheet.worksheet.side_effect = lambda name: live_ws if name == "live_activities" else expired_ws
    fake_sa.open_by_key.return_value = sheet

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    sheet.add_worksheet.reset_mock()
    live_ws.append_row.reset_mock()
    expired_ws.append_row.reset_mock()

    svc.ensureSheetsExist()

    sheet.add_worksheet.assert_not_called()
    live_ws.append_row.assert_not_called()
    expired_ws.append_row.assert_not_called()


# --------------- Testes de removePastLiveActivities ---------------

@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_removePastLiveActivities_empty_or_only_header_returns(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    live_ws.get_all_values.return_value = [["id", "name", "startDate", "community"]]

    # cria service sem executar a limpeza automaticamente
    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.removePastLiveActivities()

    assert any("Tabela live_activities vazia" in m for m in caplog.messages)
    expired_ws.append_rows.assert_not_called()
    live_ws.clear.assert_not_called()


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_removePastLiveActivities_separates_valid_and_expired_and_moves(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    now = datetime.now(timezone.utc)
    future = _iso_z(now + timedelta(hours=2))
    past = _iso_z(now - timedelta(hours=2))
    header = ["id", "name", "startDate", "community"]
    data_rows = [
        ["1", "Futuro", future, "AR SP"],
        ["2", "Passado", past, "AR SP"],
        ["3", "Invalida", "data-ruim", "AR SP"],
    ]
    live_ws.get_all_values.return_value = [header] + data_rows

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.removePastLiveActivities()

    live_ws.clear.assert_called_once()
    live_ws.append_rows.assert_called_once()
    args, kwargs = live_ws.append_rows.call_args
    written_rows = args[0]
    assert written_rows[0] == header
    assert len(written_rows) == 2  # header + 1 válida
    assert written_rows[1][0] == "1"

    expired_ws.append_rows.assert_called_once()
    exp_rows = expired_ws.append_rows.call_args[0][0]
    assert len(exp_rows) == 1 and exp_rows[0][0] == "2"

    assert any("Erro ao converter data: data-ruim" in m for m in caplog.messages)


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_removePastLiveActivities_no_expired_logs_and_returns(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    now = datetime.now(timezone.utc)
    future1 = _iso_z(now + timedelta(hours=1))
    future2 = _iso_z(now + timedelta(hours=3))
    header = ["id", "name", "startDate", "community"]
    live_ws.get_all_values.return_value = [header, ["1", "A", future1, "X"], ["2", "B", future2, "Y"]]

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.removePastLiveActivities()

    assert any("Nenhuma atividade expirada encontrada" in m for m in caplog.messages)
    live_ws.clear.assert_not_called()
    expired_ws.append_rows.assert_not_called()


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_removePastLiveActivities_fallback_when_append_to_expired_fails(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    now_aware = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    future = _iso_z(now_aware + timedelta(hours=1))
    past = _iso_z(now_aware - timedelta(hours=1))
    header = ["id", "name", "startDate", "community"]
    data_rows = [["10", "Válida", future, "C"], ["20", "Expirada", past, "C"]]
    live_ws.get_all_values.side_effect = [
        [header] + data_rows,  # primeira execução
        [header] + data_rows,  # leitura no fallback
    ]

    # A primeira tentativa em expired deve falhar; a segunda (fallback) deve funcionar
    expired_ws.append_rows.side_effect = [Exception("falha ao anexar"), None]

    # Pachar o símbolo 'datetime' dentro do módulo para o fallback usar um "aware"
    class FakeDatetime:
        @staticmethod
        def now(tz=None):
            return now_aware
        @staticmethod
        def strptime(s, fmt):
            return datetime.strptime(s, fmt)

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    with patch("Services.GoogleSheetsService.datetime", FakeDatetime):
        with caplog.at_level(logging.INFO):
            svc.removePastLiveActivities()

    assert any("Falha ao anexar em expired" in m for m in caplog.messages)
    assert live_ws.clear.call_count >= 1
    assert live_ws.append_rows.call_count >= 1


# --------------- Testes de addNewActivities ---------------

class FakeEvent:
    def __init__(self, id, name, start):
        self.id = id
        self.name = name
        self.startDate = start

class FakeCommunity:
    def __init__(self, name, events):
        self.name = name
        self.events = events
        self.set_events_called_with = None
    def setEvents(self, events):
        self.set_events_called_with = events


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_addNewActivities_no_events(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    community = FakeCommunity("AR SP", [])
    with caplog.at_level(logging.INFO):
        svc.addNewActivities(community)

    assert any("não possui atividades" in m for m in caplog.messages)
    live_ws.append_rows.assert_not_called()


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_addNewActivities_empty_sheet_raises(p_keyfile, p_authorize, logger):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    live_ws.get_all_values.return_value = []  # sem cabeçalho

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    now = datetime.now(timezone.utc)
    evt = FakeEvent("1", "Run", _iso_z(now + timedelta(hours=1)))
    community = FakeCommunity("AR SP", [evt])

    with pytest.raises(ValueError):
        svc.addNewActivities(community)


@patch("Services.GoogleSheetsService.gspread.authorize")
@patch("Services.GoogleSheetsService.ServiceAccountCredentials._from_parsed_json_keyfile")
def test_addNewActivities_appends_only_new_future_and_sets_on_community(p_keyfile, p_authorize, logger, caplog):
    fake_sa = MagicMock()
    p_authorize.return_value = fake_sa
    sheet, live_ws, expired_ws = _setup_sheet_with_tabs(fake_sa)

    now = datetime.now(timezone.utc)
    header = ["id", "name", "startDate", "community"]
    live_ws.get_all_values.return_value = [header, ["1", "Existe", _iso_z(now + timedelta(days=1)), "AR SP"]]

    evt_dup = FakeEvent("1", "Duplicado", _iso_z(now + timedelta(days=2)))
    evt_new = FakeEvent("2", "Novo Futuro", _iso_z(now + timedelta(hours=3)))
    evt_past = FakeEvent("3", "Passado", _iso_z(now - timedelta(hours=2)))
    community = FakeCommunity("AR SP", [evt_dup, evt_new, evt_past])

    with patch("Services.GoogleSheetsService.GoogleSheetsService.removePastLiveActivities", lambda self: None):
        svc = GoogleSheetsService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.addNewActivities(community)

    live_ws.append_rows.assert_called_once()
    args, kwargs = live_ws.append_rows.call_args
    rows = args[0]
    assert rows == [["2", "Novo Futuro", evt_new.startDate, "AR SP"]]
    assert kwargs.get("value_input_option") == "RAW"

    assert community.set_events_called_with is not None
    ids = [e.id for e in community.set_events_called_with]
    assert ids == ["2"]
    assert any("Foram Encontradas 1 novos eventos" in m for m in caplog.messages)