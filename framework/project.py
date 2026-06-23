import json
import os
from pathlib import Path

from dotenv import load_dotenv


class ProjectValidationError(Exception):
    pass


class MouseProject:
    def __init__(self, root=None):
        self.root = Path(root or os.getcwd()).resolve()

    @property
    def mouse_json_path(self):
        return self.root.joinpath("mouse.json")

    @property
    def env_path(self):
        return self.root.joinpath(".env")

    @property
    def framework_path(self):
        return self.root.joinpath("framework")

    @property
    def nest_path(self):
        return self.root.joinpath("framework", "nest")

    @property
    def database_core_path(self):
        return self.nest_path.joinpath("database")

    def path(self, *parts):
        return self.root.joinpath(*parts)

    def load_manifest(self):
        with self.mouse_json_path.open("r") as file:
            return json.load(file)

    def load_env(self):
        load_dotenv(self.env_path)

    def root_directory(self):
        self.load_env()
        return os.getenv("ROOT_DIRECTORY", "web").strip("'\"")

    def app_path(self, *parts):
        return self.path(self.root_directory(), *parts)

    def require(self, require_env=True, require_database=False):
        if not self.mouse_json_path.exists():
            raise ProjectValidationError(
                "'mouse.json' not found. Ensure you are in the root of a Mouse framework project."
            )

        if require_env and not self.env_path.exists():
            raise ProjectValidationError(
                "'.env' not found. Create it from '.env.example' before running this command."
            )

        if not self.nest_path.is_dir():
            raise ProjectValidationError(
                "'framework/nest' not found. Ensure this Mouse project includes the Nest core."
            )

        if require_database and not self.database_core_path.is_dir():
            raise ProjectValidationError(
                "'framework/nest/database' not found. Ensure this Mouse project includes database support."
            )

        return self


def require_mouse_project(root=None, require_env=True, require_database=False):
    return MouseProject(root).require(
        require_env=require_env,
        require_database=require_database,
    )

