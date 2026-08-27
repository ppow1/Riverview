import psycopg

from riverview.database.connection import DatabaseConfig, _connect_with_retry


def test_connect_retries_transient_operational_failure(monkeypatch):
    config = DatabaseConfig("db", 5432, "river", "app", "[REDACTED]")
    attempts = []

    class Connection:
        pass

    def connect(**kwargs):
        attempts.append(kwargs)
        if len(attempts) < 3:
            raise psycopg.OperationalError("connection timeout expired")
        return Connection()

    monkeypatch.setattr("riverview.database.connection.psycopg.connect", connect)
    monkeypatch.setattr("riverview.database.connection.time.sleep", lambda _: None)

    assert isinstance(_connect_with_retry(config), Connection)
    assert len(attempts) == 3
    assert all(item["connect_timeout"] == 5 for item in attempts)


def test_connect_does_not_retry_non_operational_database_error(monkeypatch):
    config = DatabaseConfig("db", 5432, "river", "app", "[REDACTED]")
    attempts = []

    def connect(**kwargs):
        attempts.append(kwargs)
        raise psycopg.ProgrammingError("bad startup parameter")

    monkeypatch.setattr("riverview.database.connection.psycopg.connect", connect)
    monkeypatch.setattr("riverview.database.connection.time.sleep", lambda _: None)

    try:
        _connect_with_retry(config)
    except psycopg.ProgrammingError:
        pass
    else:
        raise AssertionError("ProgrammingError should be raised immediately")
    assert len(attempts) == 1
