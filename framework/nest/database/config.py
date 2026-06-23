import os
from pathlib import Path

from dotenv import load_dotenv

from framework.project import MouseProject


def project_path(*parts):
    return MouseProject().path(*parts)


def root_directory():
    return MouseProject().root_directory()


def database_config():
    load_dotenv()

    connection = os.getenv("DB_CONNECTION", "sqlite").lower()
    database = os.getenv("DB_DATABASE", "")

    if connection == "sqlite":
        if not database:
            database = "database/database.sqlite"

        database_path = Path(database)
        if not database_path.is_absolute():
            database_path = project_path(root_directory(), database_path)

        return {
            "connection": connection,
            "database": str(database_path),
        }

    if connection == "mysql":
        return {
            "connection": connection,
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "database": database,
            "user": os.getenv("DB_USERNAME", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
        }

    raise ValueError(f"Unsupported DB_CONNECTION: {connection}")
