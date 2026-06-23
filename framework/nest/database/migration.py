import importlib.util
from pathlib import Path

from .connection import db
from .config import project_path, root_directory


class Migration:
    def up(self, database):
        raise NotImplementedError

    def down(self, database):
        raise NotImplementedError


class MigrationRepository:
    def __init__(self, database):
        self.database = database

    def create_table(self):
        if self.database.driver == "mysql":
            self.database.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    migration VARCHAR(255) NOT NULL,
                    batch INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            self.database.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration TEXT NOT NULL,
                    batch INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        self.database.commit()

    def ran(self):
        rows = self.database.query("SELECT migration FROM migrations ORDER BY id")
        return [row["migration"] for row in rows]

    def last_batch(self):
        rows = self.database.query("SELECT MAX(batch) as batch FROM migrations")
        return rows[0]["batch"] or 0

    def log(self, migration, batch):
        self.database.execute(
            "INSERT INTO migrations (migration, batch) VALUES (%s, %s)"
            if self.database.driver == "mysql"
            else "INSERT INTO migrations (migration, batch) VALUES (?, ?)",
            (migration, batch),
        )

    def delete(self, migration):
        self.database.execute(
            "DELETE FROM migrations WHERE migration = %s"
            if self.database.driver == "mysql"
            else "DELETE FROM migrations WHERE migration = ?",
            (migration,),
        )

    def migrations_for_batch(self, batch):
        rows = self.database.query(
            "SELECT migration FROM migrations WHERE batch = %s ORDER BY id DESC"
            if self.database.driver == "mysql"
            else "SELECT migration FROM migrations WHERE batch = ? ORDER BY id DESC",
            (batch,),
        )
        return [row["migration"] for row in rows]


class Migrator:
    def __init__(self, database=None, migrations_path=None):
        self.database = database or db()
        self.migrations_path = Path(
            migrations_path or project_path(root_directory(), "database", "migrations")
        )
        self.repository = MigrationRepository(self.database)

    def run(self):
        self.repository.create_table()
        ran = set(self.repository.ran())
        migrations = [
            path for path in self._migration_files()
            if path.stem not in ran
        ]

        if not migrations:
            return []

        batch = self.repository.last_batch() + 1
        migrated = []

        for path in migrations:
            migration = self._load_migration(path)
            migration.up(self.database)
            self.repository.log(path.stem, batch)
            migrated.append(path.stem)

        self.database.commit()
        return migrated

    def rollback(self):
        self.repository.create_table()
        batch = self.repository.last_batch()
        if not batch:
            return []

        migrations = self.repository.migrations_for_batch(batch)
        rolled_back = []

        for migration_name in migrations:
            path = self.migrations_path.joinpath(f"{migration_name}.py")
            migration = self._load_migration(path)
            migration.down(self.database)
            self.repository.delete(migration_name)
            rolled_back.append(migration_name)

        self.database.commit()
        return rolled_back

    def _migration_files(self):
        self.migrations_path.mkdir(parents=True, exist_ok=True)
        return sorted(self.migrations_path.glob("*.py"))

    def _load_migration(self, path):
        if not path.exists():
            raise FileNotFoundError(f"Migration not found: {path}")

        module_name = f"mouse_migration_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "Migration"):
            return module.Migration()

        if hasattr(module, "up") and hasattr(module, "down"):
            return FunctionMigration(module.up, module.down)

        raise AttributeError(
            f"{path.name} must define a Migration class or up/down functions."
        )


class FunctionMigration(Migration):
    def __init__(self, up, down):
        self._up = up
        self._down = down

    def up(self, database):
        self._up(database)

    def down(self, database):
        self._down(database)

