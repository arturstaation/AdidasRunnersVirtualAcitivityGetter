import logging
from uuid import UUID
from unittest.mock import patch

import pytest

from Services.LoggerService import LoggerService


@pytest.fixture
def no_basicConfig():
    # Evita criar arquivo application.log durante os testes
    with patch("Services.LoggerService.logging.basicConfig") as _p:
        yield _p


def test_initialization_emits_logs_with_processing_id(caplog, no_basicConfig):
    # Captura logs emitidos durante a construção
    with caplog.at_level(logging.INFO):
        svc = LoggerService()

    # Deve ter logado as duas mensagens
    messages = [rec.message for rec in caplog.records]
    assert any("Logger configurado" in m for m in messages)
    assert any("Iniciando Processamento" in m for m in messages)

    # Todos os registros desse logger devem conter o atributo processingId
    proc_id = svc.getProcessingId()
    assert isinstance(proc_id, str)
    # É uma string UUID válida?
    UUID(proc_id)  # não lança -> válido

    # Confere que os registros têm o extra processingId correto
    proc_ids_in_records = {getattr(rec, "processingId", None) for rec in caplog.records}
    assert proc_id in proc_ids_in_records


def test_third_party_loggers_set_to_warning(no_basicConfig):
    LoggerService()
    assert logging.getLogger("seleniumwire").level == logging.WARNING
    assert logging.getLogger("mitmproxy").level == logging.WARNING
    assert logging.getLogger("hpack").level == logging.WARNING


def test_console_handler_configuration(no_basicConfig):
    svc = LoggerService()

    # O base_logger é o logger do módulo Services.LoggerService (pois usa __name__)
    module_logger = logging.getLogger("Services.LoggerService")

    # Deve ter um StreamHandler com nível DEBUG e formatter contendo %(processingId)s
    stream_handlers = [h for h in module_logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) >= 0

    has_expected = False
    for h in stream_handlers:
        if h.level == logging.DEBUG and h.formatter is not None:
            fmt = h.formatter._fmt  # acessamos a string format
            if "[%(processingId)s]" in fmt and "(%(levelname)s)" in fmt and "%(asctime)s" in fmt:
                has_expected = True
                break

    assert has_expected, "Não encontrou StreamHandler com formatter contendo %(processingId)s"

    # O LoggerAdapter deve estar configurado e funcional
    adapter = svc.getLogger()
    assert isinstance(adapter, logging.LoggerAdapter)
    # O extra do adapter deve conter o processingId
    assert "processingId" in adapter.extra
    assert adapter.extra["processingId"] == svc.getProcessingId()


def test_distinct_processing_ids_between_instances(no_basicConfig):
    svc1 = LoggerService()
    svc2 = LoggerService()
    assert svc1.getProcessingId() != svc2.getProcessingId()