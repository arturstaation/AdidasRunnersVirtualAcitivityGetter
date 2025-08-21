import logging
from unittest.mock import MagicMock, patch
import pytest

from main import main as run_main


@pytest.fixture
def logger():
    lg = logging.getLogger("MainTest")
    lg.setLevel(logging.INFO)
    return lg


def _mk_community(name="AR SP"):
    comm = MagicMock()
    comm.name = name
    comm.events = []
    def _set_events(events):
        comm.events = events
    comm.setEvents.side_effect = _set_events
    return comm


@patch("main.load_dotenv")
@patch("main.asyncio.run")
@patch("main.SeleniumWebDriverService")
@patch("main.GoogleSheetsService")
@patch("main.TelegramService")
@patch("main.AdidasService")
@patch("main.UtilsService")
@patch("main.LoggerService")
def test_main_success_with_messages(p_logger_service, p_utils, p_adidas, p_telegram, p_gsheets, p_swd, p_asyncio_run, p_load_env):
    logger = logging.getLogger("MainTest.success_with_messages")
    ls_inst = MagicMock()
    ls_inst.getLogger.return_value = logger
    ls_inst.getProcessingId.return_value = "pid-123"
    p_logger_service.return_value = ls_inst

    utils_inst = MagicMock()
    p_utils.return_value = utils_inst

    tel_inst = MagicMock()
    tel_inst.generateMessage.side_effect = lambda comm, msgs: msgs + ["mensagem-formatada"]
    tel_inst.generateAdminSuccessMessage.return_value = "admin-success"
    p_telegram.return_value = tel_inst

    gs_inst = MagicMock()
    p_gsheets.return_value = gs_inst

    swd_inst = MagicMock()
    p_swd.return_value = swd_inst

    adidas_inst = MagicMock()
    comm = _mk_community()
    adidas_inst.getAdidasRunnersCommunity.return_value = [comm]
    adidas_inst.getAdidasRunnersCommunityEvents.return_value = [MagicMock()]
    p_adidas.return_value = adidas_inst

    p_asyncio_run.side_effect = lambda coro: None

    run_main()

    p_logger_service.assert_called_once()
    p_utils.assert_called_once_with(logger)
    p_load_env.assert_called_once()


    p_telegram.assert_called_once_with(logger, utils_inst)
    p_gsheets.assert_called_once_with(logger)
    p_swd.assert_called_once_with(logger, utils_inst)
    p_adidas.assert_called_once_with(logger, swd_inst)

    adidas_inst.getAdidasRunnersCommunity.assert_called_once()
    adidas_inst.getAdidasRunnersCommunityEvents.assert_called_once_with(comm)
    gs_inst.addNewActivities.assert_called_once_with(comm)
    tel_inst.generateMessage.assert_called_once()

    assert p_asyncio_run.call_count == 2
    args0 = p_asyncio_run.call_args_list[0].args[0]
    args1 = p_asyncio_run.call_args_list[1].args[0]
    tel_inst.sendTelegramMessages.assert_called_once()
    tel_inst.sendTelegramAdminMessage.assert_called_once_with("admin-success")

    swd_inst.stopDriver.assert_called_once()


@patch("main.load_dotenv")
@patch("main.asyncio.run")
@patch("main.SeleniumWebDriverService")
@patch("main.GoogleSheetsService")
@patch("main.TelegramService")
@patch("main.AdidasService")
@patch("main.UtilsService")
@patch("main.LoggerService")
def test_main_success_without_messages_sets_empty_true_and_sends_only_admin(p_logger_service, p_utils, p_adidas, p_telegram, p_gsheets, p_swd, p_asyncio_run, p_load_env):
    logger = logging.getLogger("MainTest.success_without_messages")
    ls_inst = MagicMock()
    ls_inst.getLogger.return_value = logger
    ls_inst.getProcessingId.return_value = "pid-abc"
    p_logger_service.return_value = ls_inst

    utils_inst = MagicMock()
    p_utils.return_value = utils_inst

    tel_inst = MagicMock()
    tel_inst.generateAdminSuccessMessage.return_value = "admin-success-empty"
    p_telegram.return_value = tel_inst

    gs_inst = MagicMock()
    p_gsheets.return_value = gs_inst

    swd_inst = MagicMock()
    p_swd.return_value = swd_inst

    adidas_inst = MagicMock()
    comm = _mk_community()
    adidas_inst.getAdidasRunnersCommunity.return_value = [comm]
    adidas_inst.getAdidasRunnersCommunityEvents.return_value = []
    p_adidas.return_value = adidas_inst

    p_asyncio_run.side_effect = lambda coro: None

    run_main()

    tel_inst.generateMessage.assert_not_called()
    tel_inst.sendTelegramMessages.assert_not_called()

    tel_inst.generateAdminSuccessMessage.assert_called_once()
    args, kwargs = tel_inst.generateAdminSuccessMessage.call_args
    assert args[1] is True
    tel_inst.sendTelegramAdminMessage.assert_called_once_with("admin-success-empty")

    assert p_asyncio_run.call_count == 1

    swd_inst.stopDriver.assert_called_once()


@patch("main.load_dotenv")
@patch("main.asyncio.run")
@patch("main.SeleniumWebDriverService")
@patch("main.GoogleSheetsService")
@patch("main.TelegramService")
@patch("main.AdidasService")
@patch("main.UtilsService")
@patch("main.LoggerService")
def test_main_exception_flow_sends_admin_error(p_logger_service, p_utils, p_adidas, p_telegram, p_gsheets, p_swd, p_asyncio_run, p_load_env):
    logger = logging.getLogger("MainTest.exception_flow")
    ls_inst = MagicMock()
    ls_inst.getLogger.return_value = logger
    ls_inst.getProcessingId.return_value = "pid-err"
    p_logger_service.return_value = ls_inst

    utils_inst = MagicMock()
    p_utils.return_value = utils_inst

    tel_inst_try = MagicMock()
    tel_inst_except = MagicMock()
    p_telegram.side_effect = [tel_inst_try, tel_inst_except]

    p_gsheets.return_value = MagicMock()
    p_swd.return_value = MagicMock()

    adidas_inst = MagicMock()
    p_adidas.return_value = adidas_inst
    adidas_inst.getAdidasRunnersCommunity.side_effect = Exception("boom")

    p_asyncio_run.side_effect = lambda coro: None

    run_main()

    assert p_telegram.call_count >= 2
    tel_inst_except.generateAdminErrorMessage.assert_called_once()
    p_asyncio_run.assert_called_once()
    tel_inst_except.sendTelegramAdminMessage.assert_called_once()