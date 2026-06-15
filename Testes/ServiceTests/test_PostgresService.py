import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from Services.PostgresService import PostgresService
from Models import AdidasCommunity, AdidasRunnersEvent


def _iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@pytest.fixture
def logger():
    lg = logging.getLogger("PostgresServiceTest")
    lg.setLevel(logging.INFO)
    return lg


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("PG_HOST", "adidas-db")
    monkeypatch.setenv("PG_DB", "adidas_runners")
    monkeypatch.setenv("PG_USER", "adidas")
    monkeypatch.setenv("PG_PASSWORD", "secret")
    yield


def _make_cursor():
    """Cursor mock que funciona como context manager."""
    cur = MagicMock()
    cur.__enter__ = MagicMock(return_value=cur)
    cur.__exit__ = MagicMock(return_value=False)
    cur.rowcount = 0
    return cur


@patch("Services.PostgresService.psycopg.connect")
def _build_service(p_connect, cursor):
    conn = MagicMock()
    conn.closed = False
    conn.cursor.return_value = cursor
    p_connect.return_value = conn
    lg = logging.getLogger("PostgresServiceTest.build")
    svc = PostgresService(lg)
    return svc, conn


def test_init_creates_schema_and_cleans_expired(logger):
    cur = _make_cursor()
    svc, conn = _build_service(cursor=cur)

    # _ensureSchema (CREATE TABLE + CREATE INDEX) e removePastLiveActivities (DELETE)
    executed = " ".join(call.args[0] for call in cur.execute.call_args_list)
    assert "CREATE TABLE IF NOT EXISTS activities" in executed
    assert "CREATE INDEX IF NOT EXISTS idx_activities_start_date" in executed
    assert "DELETE FROM activities WHERE start_date <= now()" in executed


def test_add_new_activities_inserts_only_future_and_unseen(logger):
    cur = _make_cursor()
    svc, conn = _build_service(cursor=cur)
    cur.execute.reset_mock()

    future = datetime.now(timezone.utc) + timedelta(days=2)
    past = datetime.now(timezone.utc) - timedelta(days=2)

    ev_new = AdidasRunnersEvent("1", "Run A", "cat", _iso_z(future))
    ev_dup = AdidasRunnersEvent("2", "Run B", "cat", _iso_z(future))
    ev_past = AdidasRunnersEvent("3", "Run C", "cat", _iso_z(past))

    comm = AdidasCommunity("c1", "SP")
    comm.setEvents([ev_new, ev_dup, ev_past])

    # id=1 é novo (RETURNING devolve linha); id=2 já existe (ON CONFLICT -> None).
    # O evento passado nem chega a executar INSERT.
    cur.fetchone.side_effect = [("1",), None]

    svc.addNewActivities(comm)

    insert_calls = [c for c in cur.execute.call_args_list if "INSERT INTO activities" in c.args[0]]
    assert len(insert_calls) == 2  # só os 2 futuros tentam inserir
    # Sobrou só o evento realmente novo para notificar no Telegram.
    assert [e.id for e in comm.events] == ["1"]


def test_add_new_activities_empty_returns_early(logger):
    cur = _make_cursor()
    svc, conn = _build_service(cursor=cur)
    cur.execute.reset_mock()

    comm = AdidasCommunity("c1", "SP")
    comm.setEvents([])

    svc.addNewActivities(comm)

    assert cur.execute.call_count == 0
    assert comm.events == []
