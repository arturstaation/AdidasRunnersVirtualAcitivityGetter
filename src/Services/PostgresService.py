import os
import traceback
from datetime import datetime, timezone
from logging import Logger
from typing import Self, List

import psycopg

from Models import AdidasCommunity, AdidasRunnersEvent


class PostgresService:
    """Persiste atividades do Adidas Runners no Postgres.

    Substitui o antigo GoogleSheetsService mantendo a mesma interface usada pelo
    main.py (addNewActivities / removePastLiveActivities). As duas abas do
    GoogleSheets (live_activities / expired_activities) viram uma única tabela
    `activities`; o conceito "live" passa a ser a query `start_date > now()`.
    """

    logger: Logger
    conn: psycopg.Connection

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self: Self, logger: Logger):
        self.logger = logger
        self.conn = self._connect()
        self._ensureSchema()
        self.removePastLiveActivities()

    def _connect(self: Self) -> psycopg.Connection:
        """Conecta usando DATABASE_URL ou as variáveis PG_*."""
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            dsn = (
                f"host={os.getenv('PG_HOST', 'adidas-db')} "
                f"port={os.getenv('PG_PORT', '5432')} "
                f"dbname={os.getenv('PG_DB', 'adidas_runners')} "
                f"user={os.getenv('PG_USER', 'adidas')} "
                f"password={os.getenv('PG_PASSWORD', '')}"
            )
        self.logger.info("Conectando ao Postgres")
        conn = psycopg.connect(dsn, autocommit=True)
        self.logger.info("Conexão com o Postgres estabelecida")
        return conn

    def _ensureSchema(self: Self):
        """Cria a tabela `activities` de forma idempotente."""
        self.logger.info("Garantindo schema da tabela activities")
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS activities (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    start_date  TIMESTAMPTZ NOT NULL,
                    community   TEXT NOT NULL,
                    notified_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_activities_start_date "
                "ON activities (start_date);"
            )

    def _parseStartDate(self: Self, raw: str) -> datetime:
        return datetime.strptime(raw, self.DATE_FORMAT).replace(tzinfo=timezone.utc)

    def removePastLiveActivities(self: Self):
        """Housekeeping: remove atividades já expiradas para manter a tabela enxuta.

        No GoogleSheets isso movia linhas de live_activities para
        expired_activities. Aqui o estado "expirado" é derivado da data, então
        apenas limpamos atividades passadas (idempotente e seguro)."""
        self.logger.info("Removendo atividades expiradas (start_date <= now)")
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM activities WHERE start_date <= now();")
                if cur.rowcount and cur.rowcount > 0:
                    self.logger.info(f"{cur.rowcount} atividades expiradas removidas")
                else:
                    self.logger.info("Nenhuma atividade expirada encontrada")
        except Exception as e:
            stacktrace = traceback.format_exc()
            self.logger.error(
                f"Erro ao remover atividades expiradas: {e}. Stacktrace: {stacktrace}"
            )

    def addNewActivities(self: Self, arCommunity: AdidasCommunity):
        """Insere atividades novas e deixa em arCommunity.events só as realmente novas.

        "Nova" = id ainda não existe na tabela E start_date no futuro. Usa
        INSERT ... ON CONFLICT DO NOTHING com RETURNING para descobrir, de forma
        atômica, quais ids foram de fato inseridos (evita duplicar notificação)."""
        if len(arCommunity.events) == 0:
            self.logger.info(f"A Comunidade {arCommunity.name} não possui atividades")
            return

        self.logger.info(f"Verificando Atividades da Comunidade {arCommunity.name}")
        now = datetime.now(timezone.utc)

        new_events: List[AdidasRunnersEvent] = []
        with self.conn.cursor() as cur:
            for event in arCommunity.events:
                try:
                    start_time = self._parseStartDate(event.startDate)
                except Exception as e:
                    stacktrace = traceback.format_exc()
                    self.logger.error(
                        f"Erro ao converter data: {event.startDate} - {e}. "
                        f"Pulando evento. Stacktrace: {stacktrace}"
                    )
                    continue

                if start_time <= now:
                    continue

                cur.execute(
                    """
                    INSERT INTO activities (id, name, start_date, community)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id;
                    """,
                    (str(event.id), event.name, start_time, arCommunity.name),
                )
                if cur.fetchone() is not None:
                    new_events.append(event)

        self.logger.info(
            f"Foram Encontradas {len(new_events)} novos eventos para comunidade "
            f"{arCommunity.name}"
        )
        arCommunity.setEvents(new_events)

    def close(self: Self):
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
        except Exception:
            pass
