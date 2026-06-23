import sqlite3
from pathlib import Path

from .config import database_config


class DatabaseConnection:
    def __init__(self, config=None):
        self.config = config or database_config()
        self.driver = self.config["connection"]
        self._connection = None

    def connect(self):
        if self._connection:
            return self

        if self.driver == "sqlite":
            database = Path(self.config["database"])
            database.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(database)
            self._connection.row_factory = sqlite3.Row
            return self

        if self.driver == "mysql":
            try:
                import mysql.connector
            except ImportError as exc:
                raise ImportError(
                    "MySQL requires mysql-connector-python. Install it with: "
                    "pip install mysql-connector-python"
                ) from exc

            self._connection = mysql.connector.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
            )
            return self

        raise ValueError(f"Unsupported database driver: {self.driver}")

    @property
    def raw(self):
        self.connect()
        return self._connection

    def cursor(self):
        self.connect()
        if self.driver == "mysql":
            return self._connection.cursor(dictionary=True)
        return self._connection.cursor()

    def execute(self, sql, params=None):
        cursor = self.cursor()
        cursor.execute(sql, params or ())
        return cursor

    def query(self, sql, params=None):
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def statement(self, sql, params=None):
        return self.execute(sql, params)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


def db():
    return DatabaseConnection().connect()


def create_database(config=None):
    config = config or database_config()
    driver = config["connection"]

    if driver == "sqlite":
        database = Path(config["database"])
        database.parent.mkdir(parents=True, exist_ok=True)
        database.touch(exist_ok=True)
        return str(database)

    if driver == "mysql":
        database = config["database"]
        if not database:
            raise ValueError("DB_DATABASE must be configured to create a MySQL database.")

        try:
            import mysql.connector
        except ImportError as exc:
            raise ImportError(
                "MySQL requires mysql-connector-python. Install it with: "
                "pip install mysql-connector-python"
            ) from exc

        connection = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
        )

        try:
            cursor = connection.cursor()
            database_identifier = str(database).replace("`", "``")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_identifier}`")
            connection.commit()
        finally:
            connection.close()

        return database

    raise ValueError(f"Unsupported database driver: {driver}")
