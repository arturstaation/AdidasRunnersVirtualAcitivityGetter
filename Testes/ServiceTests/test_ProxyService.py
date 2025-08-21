import logging
import pytest
from unittest.mock import patch, MagicMock

from Services.ProxyService import ProxyService


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("PROXY_USER", "userX")
    monkeypatch.setenv("PROXY_PASSWORD", "passX")
    yield
    monkeypatch.delenv("PROXY_USER", raising=False)
    monkeypatch.delenv("PROXY_PASSWORD", raising=False)


@pytest.fixture
def logger():
    lg = logging.getLogger("ProxyServiceTest")
    lg.setLevel(logging.INFO)
    return lg


def _mk_response(text: str):
    resp = MagicMock()
    resp.text = text
    return resp


@patch("Services.ProxyService.ProxyModel")
@patch("Services.ProxyService.socket.gethostbyname")
@patch("Services.ProxyService.requests.get")
def test_getProxies_success_with_default_port(p_get, p_dns, p_model, logger, caplog):
    p_get.side_effect = [
        _mk_response("OK"), 
        _mk_response("host.dataimpulse.net:12345:login1:password1"),  
    ]
    p_dns.return_value = "1.2.3.4"

    class FakePM:
        def __init__(self, host, port, login, password):
            self.host = host
            self.proxyPort = port
            self.login = login
            self.password = password
    p_model.side_effect = lambda h, p, u, pw: FakePM(h, p, u, pw)

    svc = ProxyService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.getProxies(quantidade=1)

    assert p_get.call_count == 2
    rotate_url = p_get.call_args_list[0].args[0]
    list_url = p_get.call_args_list[1].args[0]
    assert "rotate_ip" in rotate_url
    assert "port=10000" in rotate_url
    assert "api/list" in list_url
    assert "quantity=1" in list_url
    assert "protocol=http" in list_url
    assert svc.proxySettings is not None
    assert svc.proxySettings.host == "1.2.3.4"
    assert svc.proxySettings.proxyPort == "12345"
    assert any("Proxy obtido com sucesso" in m for m in caplog.messages)


@patch("Services.ProxyService.ProxyModel")
@patch("Services.ProxyService.socket.gethostbyname")
@patch("Services.ProxyService.requests.get")
def test_getProxies_uses_existing_proxy_port_on_rotation(p_get, p_dns, p_model, logger):
    p_get.side_effect = [
        _mk_response("OK"),  
        _mk_response("hostX:23456:login:pass"),
    ]
    p_dns.return_value = "9.9.9.9"

    class FakePM:
        def __init__(self, host, port, login, password):
            self.host = host
            self.proxyPort = port
            self.login = login
            self.password = password
    p_model.side_effect = lambda h, p, u, pw: FakePM(h, p, u, pw)

    svc = ProxyService(logger=logger)
    svc.proxySettings = FakePM("prev", "7777", "u", "p")

    svc.getProxies(quantidade=2)

    rotate_url = p_get.call_args_list[0].args[0]
    list_url = p_get.call_args_list[1].args[0]
    assert "rotate_ip" in rotate_url
    assert "port=7777" in rotate_url
    assert "quantity=2" in list_url
    assert svc.proxySettings.host == "9.9.9.9"
    assert svc.proxySettings.proxyPort == "23456"


@patch("Services.ProxyService.ProxyModel")
@patch("Services.ProxyService.socket.gethostbyname")
@patch("Services.ProxyService.requests.get")
def test_getProxies_skips_invalid_line_then_uses_valid(p_get, p_dns, p_model, logger, caplog):
    p_get.side_effect = [
        _mk_response("OK"),
        _mk_response("invalida\nhost.ok:1111:login:pwd"),
    ]
    p_dns.return_value = "2.2.2.2"
    p_model.side_effect = lambda h, p, u, pw: MagicMock(host=h, proxyPort=p, login=u, password=pw)

    svc = ProxyService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.getProxies()

    assert svc.proxySettings is not None
    assert svc.proxySettings.host == "2.2.2.2"
    assert any("Formato inválido de proxy" in m for m in caplog.messages)


@patch("Services.ProxyService.ProxyModel")
@patch("Services.ProxyService.socket.gethostbyname")
@patch("Services.ProxyService.requests.get")
def test_getProxies_dns_failure_on_first_valid_then_success_on_second(p_get, p_dns, p_model, logger, caplog):
    p_get.side_effect = [
        _mk_response("OK"),
        _mk_response("host.fail:1234:u:p\nhost.ok:5678:u2:p2"),
    ]
    p_dns.side_effect = [Exception("dns error"), "3.3.3.3"]
    p_model.side_effect = lambda h, p, u, pw: MagicMock(host=h, proxyPort=p, login=u, password=pw)

    svc = ProxyService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.getProxies()

    assert svc.proxySettings is not None
    assert svc.proxySettings.host == "3.3.3.3"
    assert any("Erro ao resolver proxy host.fail:1234:u:p" in m for m in caplog.messages)


@patch("Services.ProxyService.ProxyModel")
@patch("Services.ProxyService.socket.gethostbyname")
@patch("Services.ProxyService.requests.get")
def test_getProxies_all_invalid_lines_leaves_settings_none(p_get, p_dns, p_model, logger, caplog):
    p_get.side_effect = [
        _mk_response("OK"),
        _mk_response("a:b:c\na:b:c:d:e\n"),
    ]
    svc = ProxyService(logger=logger)

    with caplog.at_level(logging.INFO):
        svc.getProxies()

    assert svc.proxySettings is None
    assert any("Formato inválido de proxy" in m for m in caplog.messages)


@patch("Services.ProxyService.requests.get")
def test_getProxies_raises_on_network_error(p_get, logger):
    p_get.side_effect = Exception("network down")

    svc = ProxyService(logger=logger)

    with pytest.raises(Exception) as exc:
        svc.getProxies()

    assert "Erro ao obter dados do proxy" in str(exc.value)