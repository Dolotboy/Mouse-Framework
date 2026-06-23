import re
import shutil
from datetime import datetime

from .project import require_mouse_project


def snake_case(value):
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.strip("_").lower()


class ResourceGenerator:
    def __init__(self, project=None):
        self.project = project or require_mouse_project()

    def create_view(self, view_name):
        stub_path = self.project.path("framework", "stubs", "view.stub")
        if not stub_path.exists():
            raise FileNotFoundError(f"View stub not found at '{stub_path}'.")

        views_dir = self.project.app_path("views")
        views_dir.mkdir(parents=True, exist_ok=True)

        target_path = views_dir.joinpath(f"{view_name}.html")
        if target_path.exists():
            raise FileExistsError(f"The view '{view_name}' already exists.")

        shutil.copyfile(stub_path, target_path)
        return target_path

    def create_migration(self, migration_name):
        stub_path = self.project.path("framework", "stubs", "migration.stub")
        if not stub_path.exists():
            raise FileNotFoundError(f"Migration stub not found at '{stub_path}'.")

        migrations_dir = self.project.app_path("database", "migrations")
        migrations_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        target_path = migrations_dir.joinpath(f"{timestamp}_{snake_case(migration_name)}.py")

        shutil.copyfile(stub_path, target_path)
        return target_path

