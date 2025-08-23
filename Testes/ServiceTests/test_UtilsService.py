import logging
import pytest
from unittest.mock import MagicMock

from Services.UtilsService import UtilsService


@pytest.fixture
def logger():
    lg = logging.getLogger("UtilsServiceTest")
    lg.setLevel(logging.INFO)
    return lg


def test_formatDate_with_Z_suffix(logger):
    svc = UtilsService(logger=logger)
    out = svc.formatDate("2025-01-02T03:04:05Z")
    assert out == "02/01/2025 às 03:04"


def test_formatDate_with_explicit_utc_offset(logger):
    svc = UtilsService(logger=logger)
    out = svc.formatDate("2025-01-02T03:04:05+00:00")
    assert out == "02/01/2025 às 03:04"


def test_formatDate_with_non_utc_offset(logger):
    svc = UtilsService(logger=logger)
    out = svc.formatDate("2025-01-02T03:04:05+03:00")
    assert out == "02/01/2025 às 03:04"


def test_formatDate_without_milliseconds(logger):
    svc = UtilsService(logger=logger)
    out = svc.formatDate("2024-12-31T23:59:00Z")
    assert out == "31/12/2024 às 23:59"


def test_formatDate_with_milliseconds(logger):
    svc = UtilsService(logger=logger)
    out = svc.formatDate("2024-07-15T12:34:56.789Z")
    assert out == "15/07/2024 às 12:34"


def test_formatDate_leap_day(logger):
    svc = UtilsService(logger=logger)
    out = svc.formatDate("2024-02-29T00:00:00Z")
    assert out == "29/02/2024 às 00:00"


def test_formatDate_invalid_input_raises(logger):
    svc = UtilsService(logger=logger)
    with pytest.raises(ValueError):
        svc.formatDate("invalid-date")


def test_formatDate_logs_message(monkeypatch):
    fake_logger = MagicMock()
    svc = UtilsService(logger=fake_logger)
    iso = "2025-01-02T03:04:05Z"
    _ = svc.formatDate(iso)
    fake_logger.info.assert_called_once()
    called_msg = fake_logger.info.call_args.args[0]
    assert "Formatando Data" in called_msg
    assert iso in called_msg

@pytest.fixture
def logger():
    lg = logging.getLogger("UtilsServiceTest")
    lg.setLevel(logging.INFO)
    return lg

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    keys = [
        "GOOGLE_CREDENTIALS",
        "GOOGLE_SHEET_ID",
        "TOKEN",
        "CHAT_ID",
        "ADMIN_CHAT_ID",
        "PROXY_ENABLED",
        "PROXY_USER",
        "PROXY_PASSWORD",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield
    for k in keys:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.parametrize(
    "input_iso, expected",
    [
        ("2024-01-02T03:04:05Z", "02/01/2024 às 03:04"),
        ("2025-08-23T15:30:00+00:00", "23/08/2025 às 15:30"),
        ("2023-12-31T23:59:59+00:00", "31/12/2023 às 23:59"),
    ],
)
def test_formatDate_formats_correctly(logger, input_iso, expected, caplog):
    us = UtilsService(logger)
    with caplog.at_level(logging.INFO):
        out = us.formatDate(input_iso)
    assert out == expected
    assert any(f"Formatando Data {input_iso}" in m for m in caplog.messages)


@pytest.mark.parametrize(
    "s, expected",
    [
        ("1", True),
        ("true", True),
        ("TRUE", True),
        ("t", True),
        ("yes", True),
        ("Y", True),
        ("on", True),
        (" On  ", True),
        ("0", False),
        ("false", False),
        ("no", False),
        ("off", False),
        ("", False),
        ("  ", False),
        ("random", False),
    ],
)
def test_strToBool_cases(logger, s, expected):
    us = UtilsService(logger)
    assert us.strToBool(s) is expected


def test_validateEnvVariables_all_required_present_proxy_disabled_warns_proxy(logger, monkeypatch, caplog):
    monkeypatch.setenv("GOOGLE_CREDENTIALS", "x")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "y")
    monkeypatch.setenv("TOKEN", "t")
    monkeypatch.setenv("CHAT_ID", "c")
    monkeypatch.setenv("PROXY_ENABLED", "false")

    us = UtilsService(logger)
    with caplog.at_level(logging.WARNING):
        us.validateEnvVariables()

    msgs = " | ".join(caplog.messages)
    assert "ADMIN_CHAT_ID (Chat de Administrador) não configurado" in msgs
    assert "Proxy desabilitado" in msgs

def test_validateEnvVariables_missing_required_vars_raises(logger, caplog):
    us = UtilsService(logger)
    with pytest.raises(Exception) as exc:
        us.validateEnvVariables()
    msg = str(exc.value)
    assert "As seguintes variáveis de ambiente não estão configuradas:" in msg
    for var in ["CHAT_ID", "GOOGLE_CREDENTIALS", "GOOGLE_SHEET_ID", "TOKEN"]:
        assert var in msg

def test_validateEnvVariables_admin_chat_id_blank_warns(logger, monkeypatch, caplog):

    monkeypatch.setenv("GOOGLE_CREDENTIALS", "gc")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "gs")
    monkeypatch.setenv("TOKEN", "tk")
    monkeypatch.setenv("CHAT_ID", "cid")

    monkeypatch.setenv("ADMIN_CHAT_ID", "   ")

    monkeypatch.setenv("PROXY_ENABLED", "False")

    us = UtilsService(logger)
    with caplog.at_level(logging.WARNING):
        us.validateEnvVariables()
    assert any("ADMIN_CHAT_ID (Chat de Administrador) não configurado" in m for m in caplog.messages)
    assert any("Proxy desabilitado" in m for m in caplog.messages)

@pytest.mark.parametrize("flag", ["1", "true", "TRUE", "Yes", "on", " y "])
def test_validateEnvVariables_proxy_enabled_requires_user_and_password_missing_raises(logger, monkeypatch, flag):

    monkeypatch.setenv("GOOGLE_CREDENTIALS", "gc")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "gs")
    monkeypatch.setenv("TOKEN", "tk")
    monkeypatch.setenv("CHAT_ID", "cid")

    monkeypatch.setenv("ADMIN_CHAT_ID", "admin")

    monkeypatch.setenv("PROXY_ENABLED", flag)

    us = UtilsService(logger)
    with pytest.raises(Exception) as exc:
        us.validateEnvVariables()
    msg = str(exc.value)
    assert "PROXY_USER" in msg and "PROXY_PASSWORD" in msg

def test_validateEnvVariables_proxy_enabled_with_user_but_no_password_raises(logger, monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS", "gc")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "gs")
    monkeypatch.setenv("TOKEN", "tk")
    monkeypatch.setenv("CHAT_ID", "cid")
    monkeypatch.setenv("ADMIN_CHAT_ID", "admin")
    monkeypatch.setenv("PROXY_ENABLED", "true")
    monkeypatch.setenv("PROXY_USER", "userx")

    us = UtilsService(logger)
    with pytest.raises(Exception) as exc:
        us.validateEnvVariables()
    msg = str(exc.value)
    assert "PROXY_USER" not in msg
    assert "PROXY_PASSWORD" in msg

def test_validateEnvVariables_proxy_enabled_with_password_but_no_user_raises(logger, monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS", "gc")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "gs")
    monkeypatch.setenv("TOKEN", "tk")
    monkeypatch.setenv("CHAT_ID", "cid")
    monkeypatch.setenv("ADMIN_CHAT_ID", "admin")
    monkeypatch.setenv("PROXY_ENABLED", "true")
    monkeypatch.setenv("PROXY_PASSWORD", "passx")

    us = UtilsService(logger)
    with pytest.raises(Exception) as exc:
        us.validateEnvVariables()
    msg = str(exc.value)
    assert "PROXY_PASSWORD" not in msg
    assert "PROXY_USER" in msg

def test_validateEnvVariables_proxy_enabled_with_both_ok_passes(logger, monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS", "gc")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "gs")
    monkeypatch.setenv("TOKEN", "tk")
    monkeypatch.setenv("CHAT_ID", "cid")
    monkeypatch.setenv("ADMIN_CHAT_ID", "admin")
    monkeypatch.setenv("PROXY_ENABLED", "true")
    monkeypatch.setenv("PROXY_USER", "userx")
    monkeypatch.setenv("PROXY_PASSWORD", "passx")

    us = UtilsService(logger)
    us.validateEnvVariables()