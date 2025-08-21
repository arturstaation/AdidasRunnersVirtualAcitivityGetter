import logging
import pytest
from unittest.mock import MagicMock

from Services.AdidasService import AdidasService
from Models import AdidasCommunity, AdidasRunnersEvent


@pytest.fixture
def logger():
    lg = logging.getLogger("AdidasServiceTest")
    lg.setLevel(logging.INFO)
    return lg


@pytest.fixture
def selenium_mock():
    return MagicMock()


@pytest.fixture
def service(logger, selenium_mock):
    return AdidasService(logger=logger, seleniumWebDriverService=selenium_mock)


@pytest.fixture
def community_sp():
    return AdidasCommunity("sp", "Adidas Runners São Paulo")


def test_get_communities_builds_list(service, selenium_mock, caplog):
    payload = {
        "_embedded": {
            "communities": [
                {"id": "1", "name": "AR São Paulo"},
                {"id": "2", "name": "AR Rio de Janeiro"},
            ]
        }
    }
    selenium_mock.getJsonFromUrl.return_value = payload

    with caplog.at_level(logging.INFO):
        result = service.getAdidasRunnersCommunity()

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], AdidasCommunity)
    assert result[0].id == "1"
    assert result[0].name == "Adidas Runners AR São Paulo"
    assert result[1].id == "2"
    assert result[1].name == "Adidas Runners AR Rio de Janeiro"

    expected_url = "https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/connect/communities?limit=100&type=AdidasRunners"
    selenium_mock.getJsonFromUrl.assert_called_once_with(expected_url)

    assert any("Obtendo dados das comunidades Adidas Runners" in m for m in caplog.messages)
    assert any("Criando lista de comunidades" in m for m in caplog.messages)


def test_get_communities_empty_list(service, selenium_mock):
    selenium_mock.getJsonFromUrl.return_value = {"_embedded": {"communities": []}}

    result = service.getAdidasRunnersCommunity()

    assert result == []


def test_get_communities_missing_embedded_raises(service, selenium_mock):
    selenium_mock.getJsonFromUrl.return_value = {}

    with pytest.raises(KeyError):
        service.getAdidasRunnersCommunity()


def test_get_events_filters_virtual(service, selenium_mock, community_sp, caplog):
    payload = {
        "_embedded": {
            "events": [
                {
                    "id": "e1",
                    "title": "Treino Virtual 5K",
                    "category": "RUN",
                    "eventStartDate": "2025-01-01T10:00:00Z",
                    "meta": {},
                },
                {
                    "id": "e2",
                    "title": "Longão 15K Presencial",
                    "category": "RUN",
                    "eventStartDate": "2025-01-02T08:00:00Z",
                    "meta": {"adidas_runners_locations": [{"city": "São Paulo"}]},
                },
                {
                    "id": "e3",
                    "title": "Yoga em Casa",
                    "category": "TRAINING",
                    "eventStartDate": "2025-01-03T19:00:00Z",
                },
            ]
        }
    }
    selenium_mock.getJsonFromUrl.return_value = payload

    with caplog.at_level(logging.INFO):
        events = service.getAdidasRunnersCommunityEvents(community_sp)

    assert isinstance(events, list)
    assert len(events) == 2
    assert all(isinstance(ev, AdidasRunnersEvent) for ev in events)
    ids = {ev.id for ev in events}
    assert ids == {"e1", "e3"}

    expected_url = f"https://www.adidas.com.br/adidasrunners/ar-api/gw/default/gw-api/v2/events/communities/{community_sp.id}?countryCodes=BR"
    selenium_mock.getJsonFromUrl.assert_called_once_with(expected_url)

    assert any(f"Obtendo dados Eventos da Comunidade {community_sp.name}" in m for m in caplog.messages)
    assert any(f"Criando Lista de Eventos da Comunidade {community_sp.name}" in m for m in caplog.messages)


def test_get_events_none_virtual_logs_empty(service, selenium_mock, community_sp, caplog):
    payload = {
        "_embedded": {
            "events": [
                {
                    "id": "e10",
                    "title": "Presencial 1",
                    "category": "RUN",
                    "eventStartDate": "2025-01-05T10:00:00Z",
                    "meta": {"adidas_runners_locations": [{"city": "São Paulo"}]},
                },
                {
                    "id": "e11",
                    "title": "Presencial 2",
                    "category": "RUN",
                    "eventStartDate": "2025-01-06T10:00:00Z",
                    "meta": {"adidas_runners_locations": [{"city": "Rio de Janeiro"}]},
                },
            ]
        }
    }
    selenium_mock.getJsonFromUrl.return_value = payload

    with caplog.at_level(logging.INFO):
        events = service.getAdidasRunnersCommunityEvents(community_sp)

    assert events == []
    assert any(
        f"Nenhum Evento Virtual Foi encontrado para a comunidade {community_sp.name}" in m
        for m in caplog.messages
    )


def test_get_events_missing_embedded_raises(service, selenium_mock, community_sp):
    selenium_mock.getJsonFromUrl.return_value = {}

    with pytest.raises(KeyError):
        service.getAdidasRunnersCommunityEvents(community_sp)