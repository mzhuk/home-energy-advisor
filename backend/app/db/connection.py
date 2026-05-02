import sqlite3
from pathlib import Path


def sqlite_path_from_url(database_url: str) -> str:
    if database_url == "sqlite:///:memory:":
        return ":memory:"

    if database_url.startswith("sqlite:////"):
        return f"/{database_url.removeprefix('sqlite:////')}"

    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")

    msg = "Only sqlite:/// database URLs are supported."
    raise ValueError(msg)


def connect(database_url: str) -> sqlite3.Connection:
    database_path = sqlite_path_from_url(database_url)
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

