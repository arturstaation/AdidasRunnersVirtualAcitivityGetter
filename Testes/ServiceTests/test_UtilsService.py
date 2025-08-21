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