import logging
import os
import html
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from Services.TelegramService import TelegramService


# ---------------- Fixtures ----------------

@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("TOKEN", "fake-token")
    monkeypatch.setenv("CHAT_ID", "12345")
    monkeypatch.setenv("ADMIN_CHAT_ID", "9999")
    yield
    monkeypatch.delenv("TOKEN", raising=False)
    monkeypatch.delenv("CHAT_ID", raising=False)
    monkeypatch.delenv("ADMIN_CHAT_ID", raising=False)


@pytest.fixture
def logger():
    lg = logging.getLogger("TelegramServiceTest")
    lg.setLevel(logging.INFO)
    return lg


@pytest.fixture
def utils():
    u = MagicMock()
    u.formatDate.side_effect = lambda s: f"[{s}]"
    return u


# ---------------- Helpers ----------------

class FakeEvent:
    def __init__(self, id, name, category, startDate):
        self.id = id
        self.name = name
        self.category = category
        self.startDate = startDate


class FakeCommunity:
    def __init__(self, name, events):
        self.name = name
        self.events = events


def _mk_bot():
    # Cria um bot que funciona como context manager assíncrono
    bot = AsyncMock()
    bot.__aenter__.return_value = bot
    bot.__aexit__.return_value = False
    bot.sendMessage = AsyncMock()
    return bot


# ---------------- Tests: generateMessage ----------------

@patch("Services.TelegramService.telegram.Bot")
def test_generateMessage_first_message_header_and_content(p_bot, logger, utils):
    p_bot.return_value = _mk_bot()
    comm = FakeCommunity(
        "AR SP",
        [FakeEvent("1", "Corrida Leve", "Run", "2025-01-01T10:00:00Z")]
    )

    svc = TelegramService(logger=logger, utilsService=utils)

    messages = []
    result = svc.generateMessage(comm, messages)

    # Deve retornar a lista de mensagens (mesma referência)
    assert result is messages
    assert len(messages) == 1
    msg = messages[0]
    # Checa cabeçalho da primeira mensagem
    assert "<b>📢 Novas atividades do Adidas Runners:</b>" in msg
    assert "<b>AR SP</b>" in msg
    # Conteúdo do evento com formatação e link
    assert "<b>• Nome:</b> Corrida Leve" in msg
    assert "<b>• Categoria:</b> Run" in msg
    assert "<b>• Início:</b> [2025-01-01T10:00:00Z]" in msg
    assert 'href="https://www.adidas.com.br/adidasrunners/events/event/1"' in msg


@patch("Services.TelegramService.telegram.Bot")
def test_generateMessage_appends_when_under_limit(p_bot, logger, utils):
    p_bot.return_value = _mk_bot()
    svc = TelegramService(logger=logger, utilsService=utils)

    # Mensagem inicial já existente (abaixo do limite)
    messages = ["<b>📢 Novas atividades do Adidas Runners:</b>\n\n<b>AR SP</b>\n\n"]
    # Nova comunidade para ser concatenada (não vazia -> sem a primeira linha geral)
    comm = FakeCommunity(
        "AR SP",
        [FakeEvent("2", "Trote", "Run", "2025-01-02T10:00:00Z")]
    )

    result = svc.generateMessage(comm, messages)

    assert result is messages
    assert len(messages) == 1  # concatenou e não criou nova
    assert "<b>AR SP</b>" in messages[0]  # título da comunidade adicionada
    assert "Trote" in messages[0]  # conteúdo do evento


@patch("Services.TelegramService.telegram.Bot")
def test_generateMessage_creates_new_when_exceeds_4096(p_bot, logger, utils):
    p_bot.return_value = _mk_bot()
    svc = TelegramService(logger=logger, utilsService=utils)

    # Força o limite: se o último item já tem 4096 chars, qualquer novo conteúdo dispara nova mensagem
    messages = ["x" * 4096]
    comm = FakeCommunity(
        "AR RJ",
        [FakeEvent("3", "Longão", "Run", "2025-01-03T10:00:00Z")]
    )

    result = svc.generateMessage(comm, messages)

    assert result is messages
    assert len(messages) == 2  # criou nova mensagem
    assert messages[1].startswith("<b>AR RJ</b>")
    assert "Longão" in messages[1]


# ---------------- Tests: sendTelegramMessages ----------------

@pytest.mark.asyncio
@patch("Services.TelegramService.telegram.Bot")
def test_sendTelegramMessages_sends_each_message(p_bot, logger, utils):
    bot = _mk_bot()
    p_bot.return_value = bot

    svc = TelegramService(logger=logger, utilsService=utils)

    msgs = ["msg1", "msg2", "msg3"]
    asyncio.run(svc.sendTelegramMessages(msgs))

    # Deve ter chamado sendMessage para cada mensagem com chat_id e parse_mode HTML
    assert bot.sendMessage.await_count == 3
    called_args = [call.kwargs for call in bot.sendMessage.await_args_list]
    for i, kwargs in enumerate(called_args):
        assert kwargs["chat_id"] == os.getenv("CHAT_ID")
        assert kwargs["text"] == msgs[i]
        assert kwargs["parse_mode"] == "HTML"


# ---------------- Tests: sendTelegramAdminMessage ----------------

@pytest.mark.asyncio
@patch("Services.TelegramService.telegram.Bot")
def test_sendTelegramAdminMessage_sends_to_admin(p_bot, logger, utils):
    bot = _mk_bot()
    p_bot.return_value = bot

    svc = TelegramService(logger=logger, utilsService=utils)

    asyncio.run(svc.sendTelegramAdminMessage("hello-admin"))

    bot.sendMessage.assert_awaited_once()
    kwargs = bot.sendMessage.await_args.kwargs
    assert kwargs["chat_id"] == os.getenv("ADMIN_CHAT_ID")
    assert kwargs["text"] == "hello-admin"
    assert kwargs["parse_mode"] == "HTML"


# ---------------- Tests: generateAdminErrorMessage ----------------

@patch("Services.TelegramService.telegram.Bot")
def test_generateAdminErrorMessage_escapes_and_truncates(p_bot, logger, utils):
    p_bot.return_value = _mk_bot()
    svc = TelegramService(logger=logger, utilsService=utils)

    processing_id = "11111111-2222-3333-4444-555555555555"
    # Monta textos com caracteres que precisam de escape
    err_text = "<bad & error>"
    stack_text = "<stack & trace>"

    # Teste sem ultrapassar limites
    msg = svc.generateAdminErrorMessage(processing_id, Exception(err_text), stack_text)
    assert "<b>❌ Erro de processamento</b>" in msg
    # Deve escapar
    assert html.escape(err_text) in msg
    assert html.escape(stack_text) in msg
    # Inclui PID escapado e em <code>
    assert f"<code>{html.escape(str(processing_id))}</code>" in msg

    # Teste com truncamento
    long_err = "E" * 900
    long_stack = "S" * 4000
    msg2 = svc.generateAdminErrorMessage(processing_id, Exception(long_err), long_stack)
    assert "E" * 800 in msg2
    assert "...[truncated]" in msg2
    assert "S" * 3500 in msg2


# ---------------- Tests: generateAdminSuccessMessage ----------------

@patch("Services.TelegramService.telegram.Bot")
def test_generateAdminSuccessMessage_includes_empty_when_true(p_bot, logger, utils):
    p_bot.return_value = _mk_bot()
    svc = TelegramService(logger=logger, utilsService=utils)

    pid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    msg_true = svc.generateAdminSuccessMessage(pid, True)
    assert "✅ Processamento Finalizado com Sucesso" in msg_true
    assert f"<code>{html.escape(pid)}</code>" in msg_true
    assert "não encontrou nenhuma nova atividade" in msg_true

    msg_false = svc.generateAdminSuccessMessage(pid, False)
    assert "✅ Processamento Finalizado com Sucesso" in msg_false
    assert f"<code>{html.escape(pid)}</code>" in msg_false
    assert "não encontrou nenhuma nova atividade" not in msg_false