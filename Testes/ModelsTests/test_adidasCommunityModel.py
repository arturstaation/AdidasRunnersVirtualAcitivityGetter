import pytest
from unittest.mock import MagicMock

from Models.adidasCommunityModel import AdidasCommunity


def test_init_sets_id_and_prefixed_name():
    comm = AdidasCommunity(id="sp", name="São Paulo")
    assert comm.id == "sp"
    assert comm.name == "Adidas Runners São Paulo"


def test_setEvents_assigns_list_reference_and_contents():
    comm = AdidasCommunity(id="rj", name="Rio de Janeiro")
    e1 = MagicMock()
    e2 = MagicMock()
    events = [e1, e2]

    comm.setEvents(events)

    # Atribui a mesma referência (não copia)
    assert comm.events is events
    # Mantém os itens e a ordem
    assert comm.events[0] is e1
    assert comm.events[1] is e2


def test_setEvents_accepts_empty_list():
    comm = AdidasCommunity(id="poa", name="Porto Alegre")
    empty = []
    comm.setEvents(empty)
    assert comm.events is empty
    assert comm.events == []


def test_multiple_instances_are_independent():
    c1 = AdidasCommunity(id="sp", name="São Paulo")
    c2 = AdidasCommunity(id="rj", name="Rio")
    assert c1.id != c2.id
    assert c1.name != c2.name

    ev1 = [MagicMock()]
    ev2 = [MagicMock(), MagicMock()]
    c1.setEvents(ev1)
    c2.setEvents(ev2)

    assert c1.events is ev1
    assert c2.events is ev2