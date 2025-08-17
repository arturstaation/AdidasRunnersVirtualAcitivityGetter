import pytest

from Models.proxyModel import ProxyModel


def test_init_sets_all_fields_correctly():
    pm = ProxyModel(pAddress="1.2.3.4", pPort="8080", pUser="user", pPassword="pass")
    assert pm.proxyAddress == "1.2.3.4"
    assert pm.proxyPort == "8080"
    assert pm.proxyUser == "user"
    assert pm.proxyPassword == "pass"


def test_port_is_kept_as_string():
    pm = ProxyModel("host.example", "7777", "login", "secret")
    assert isinstance(pm.proxyPort, str)
    assert pm.proxyPort == "7777"


def test_allows_empty_and_special_characters():
    pm = ProxyModel(pAddress="", pPort="", pUser="u$er:name", pPassword="p@ss:word#123")
    assert pm.proxyAddress == ""
    assert pm.proxyPort == ""
    assert pm.proxyUser == "u$er:name"
    assert pm.proxyPassword == "p@ss:word#123"


def test_multiple_instances_are_independent():
    a = ProxyModel("a.addr", "1000", "ua", "pa")
    b = ProxyModel("b.addr", "2000", "ub", "pb")
    assert (a.proxyAddress, a.proxyPort, a.proxyUser, a.proxyPassword) != \
           (b.proxyAddress, b.proxyPort, b.proxyUser, b.proxyPassword)