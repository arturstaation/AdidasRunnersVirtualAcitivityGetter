import json
import logging
from unittest.mock import patch, MagicMock
import types
import pytest

from Services.SeleniumWebDriverService import SeleniumWebDriverService


@pytest.fixture
def logger():
    lg = logging.getLogger("SeleniumWebDriverServiceTest")
    lg.setLevel(logging.INFO)
    return lg


def _make_proxy_settings():
    ps = MagicMock()
    ps.proxyUser = "user"
    ps.proxyPassword = "pass"
    ps.proxyAddress = "1.2.3.4"
    ps.proxyPort = "8080"
    return ps


def _patch_driver_stack(win_or_linux="win"):
    """
    Prepara patches de: Options, Service, webdriver.Chrome, ProxyService, sys.platform, TimeoutException.
    Retorna (patchers, mocks_ns) onde mocks_ns permite acesso por atributo (ponto).
    """
    options_mock_cls = MagicMock()
    options_mock = MagicMock()
    options_mock_cls.return_value = options_mock

    service_mock_cls = MagicMock()
    service_mock = MagicMock()
    service_mock_cls.return_value = service_mock

    chrome_mock_cls = MagicMock()
    driver_mock = MagicMock()
    chrome_mock_cls.return_value = driver_mock

    proxy_service_cls = MagicMock()
    proxy_service_inst = MagicMock()
    proxy_service_cls.return_value = proxy_service_inst
    proxy_service_inst.getProxySettings.return_value = _make_proxy_settings()

    class FakeTimeoutException(Exception):
        pass

    class FakeSys:
        platform = "win32" if win_or_linux == "win" else "linux"

    patchers = [
        patch("Services.SeleniumWebDriverService.Options", options_mock_cls),
        patch("Services.SeleniumWebDriverService.Service", service_mock_cls),
        patch("Services.SeleniumWebDriverService.webdriver.Chrome", chrome_mock_cls),
        patch("Services.SeleniumWebDriverService.ProxyService", proxy_service_cls),
        patch("Services.SeleniumWebDriverService.sys", FakeSys),
        patch("Services.SeleniumWebDriverService.TimeoutException", FakeTimeoutException),
    ]

    mocks_ns = types.SimpleNamespace(
        options_cls=options_mock_cls,
        options=options_mock,
        service_cls=service_mock_cls,
        service=service_mock,
        chrome_cls=chrome_mock_cls,
        driver=driver_mock,
        proxy_cls=proxy_service_cls,
        proxy=proxy_service_inst,
        TimeoutException=FakeTimeoutException,
        sys=FakeSys,
    )
    return patchers, mocks_ns


def test_getDriver_windows_builds_chrome_with_proxy(logger):
    patchers, m = _patch_driver_stack(win_or_linux="win")
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        m.service_cls.assert_called_once()
        assert m.service_cls.call_args.kwargs.get("executable_path") == "../chromedriver.exe"

        m.proxy_cls.assert_called_once()
        m.proxy.getProxies.assert_called_once()

        _, kwargs = m.chrome_cls.call_args
        seleniumwire_options = kwargs.get("seleniumwire_options")
        proxy_url = seleniumwire_options["proxy"]["http"]
        assert proxy_url == "http://user:pass@1.2.3.4:8080"
        assert seleniumwire_options["proxy"]["https"] == proxy_url

        assert svc.driver is m.driver


def test_getDriver_linux_builds_chrome_with_proxy(logger):
    patchers, m = _patch_driver_stack(win_or_linux="linux")
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        m.service_cls.assert_called_once()
        assert m.service_cls.call_args.kwargs.get("executable_path") == "../chromedriver"
        m.proxy.getProxies.assert_called_once()
        _, kwargs = m.chrome_cls.call_args
        assert kwargs["seleniumwire_options"]["proxy"]["http"] == "http://user:pass@1.2.3.4:8080"


def test_getJsonFromUrl_success_first_try(logger):
    patchers, m = _patch_driver_stack()
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        pre = MagicMock()
        pre.text = json.dumps({"ok": True, "n": 1})
        m.driver.find_element.return_value = pre

        with patch.object(SeleniumWebDriverService, "restartDriver") as p_restart:
            data = svc.getJsonFromUrl("http://example.com/api", tentativas=3)
            assert data == {"ok": True, "n": 1}
            m.driver.get.assert_called_once_with("http://example.com/api")
            p_restart.assert_not_called()


def test_getJsonFromUrl_403_then_success(logger):
    patchers, m = _patch_driver_stack()
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        m.driver.find_element.side_effect = [
            m.TimeoutException("no <pre>"),
            MagicMock(text=json.dumps({"try": 2})),
        ]

        with patch.object(SeleniumWebDriverService, "restartDriver") as p_restart:
            data = svc.getJsonFromUrl("http://example.com/api", tentativas=3)
            assert data == {"try": 2}
            assert m.driver.get.call_count == 2
            p_restart.assert_called_once()


def test_getJsonFromUrl_all_403_raises(logger):
    patchers, m = _patch_driver_stack()
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        m.driver.find_element.side_effect = m.TimeoutException("again")

        with patch.object(SeleniumWebDriverService, "restartDriver") as p_restart:
            with pytest.raises(Exception) as exc:
                svc.getJsonFromUrl("http://example.com/api", tentativas=2)
            assert "Falha ao obter JSON de http://example.com/api após 2 tentativas" in str(exc.value)
            assert p_restart.call_count == 2


def test_getJsonFromUrl_unexpected_error_then_success(logger):
    patchers, m = _patch_driver_stack()
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        m.driver.get.side_effect = [Exception("network hiccup"), None]
        m.driver.find_element.return_value = MagicMock(text=json.dumps({"ok": "after retry"}))

        with patch.object(SeleniumWebDriverService, "restartDriver") as p_restart:
            data = svc.getJsonFromUrl("http://example.com/api", tentativas=3)
            assert data == {"ok": "after retry"}
            assert m.driver.get.call_count == 2
            p_restart.assert_called_once()


def test_stopDriver_calls_quit(logger):
    with patch.object(SeleniumWebDriverService, "getDriver", lambda self: None):
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())
    drv = MagicMock()
    svc.driver = drv

    svc.stopDriver()
    drv.quit.assert_called_once()


def test_restartDriver_calls_stop_and_getDriver_even_if_stop_raises(logger):
    with patch.object(SeleniumWebDriverService, "getDriver", lambda self: None):
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

    with patch.object(SeleniumWebDriverService, "stopDriver", side_effect=Exception("ignore")), \
         patch.object(SeleniumWebDriverService, "getDriver") as p_get:
        svc.restartDriver()
        p_get.assert_called_once()

def test_getJsonFromUrl_page_load_timeout_then_success(logger):
    """
    Cobre linhas 81-82: warning 'A pagina ... não carregou a tempo' e raise TimeoutException.
    Na primeira tentativa, driver.get levanta TimeoutException; depois reinicia e tem sucesso.
    """
    patchers, m = _patch_driver_stack()
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        # Primeira chamada a get levanta TimeoutException; segunda funciona
        m.driver.get.side_effect = [m.TimeoutException("timeout on load"), None]

        # Quando carrega com sucesso, há um <pre> válido
        pre = MagicMock()
        pre.text = json.dumps({"ok": True, "after": "timeout"})
        # Usando o mesmo padrão dos seus testes pré-existentes (find_element)
        m.driver.find_element.return_value = pre

        with patch.object(SeleniumWebDriverService, "restartDriver") as p_restart:
            data = svc.getJsonFromUrl("http://example.com/api", tentativas=3)
            assert data == {"ok": True, "after": "timeout"}
            # get chamado duas vezes: 1a falha por TimeoutException, 2a sucesso
            assert m.driver.get.call_count == 2
            # Após a TimeoutException, deve reiniciar o driver uma vez
            p_restart.assert_called_once()


def test_getJsonFromUrl_unknown_error_on_pre_then_success(logger):
    """
    Cobre linhas 93-95: warning 'Erro desconhecido...' e raise Exception('Erro Desconhecido').
    Na primeira tentativa, ocorre erro ao acessar/preparar o <pre> (ex.: ao ler .text).
    Depois reinicia e tem sucesso.
    """
    patchers, m = _patch_driver_stack()
    with patchers[0], patchers[1], patchers[2], patchers[3], patchers[4], patchers[5]:
        svc = SeleniumWebDriverService(logger=logger, utilsService=MagicMock())

        # Simula get ok em ambas as tentativas
        m.driver.get.side_effect = [None, None]

        # Primeiro ciclo: o elemento <pre> existe, mas ao acessar .text ocorre erro inesperado
        pre_broken = MagicMock()
        type(pre_broken).text = property(lambda self: (_ for _ in ()).throw(Exception("unexpected pre error")))

        # Segundo ciclo: sucesso ao obter o JSON
        pre_ok = MagicMock()
        pre_ok.text = json.dumps({"ok": True, "after": "unknown-error"})

        # Alterna o retorno do find_element entre "quebrado" e "ok"
        m.driver.find_element.side_effect = [pre_broken, pre_ok]

        with patch.object(SeleniumWebDriverService, "restartDriver") as p_restart:
            data = svc.getJsonFromUrl("http://example.com/api", tentativas=3)
            assert data == {"ok": True, "after": "unknown-error"}
            # get chamado duas vezes: 1a tentativa com erro interno, 2a sucesso
            assert m.driver.get.call_count == 2
            # Deve reiniciar após o erro desconhecido
            p_restart.assert_called_once()