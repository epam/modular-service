import os
from pathlib import Path
import sys

SOURCE = Path(__file__).parent.parent / 'src'


class ImportFromContext:
    """
    Context object to import lambdas and packages. It's necessary because
    root path is not the path to the syndicate project but the path where
    lambdas are accumulated - SRC_FOLDER
    """

    def __init__(self, source: Path, envs: dict):
        self.envs = envs or {}
        self._old_envs = {}
        self.source = str(source.resolve())

    def add_source_to_path(self):
        if self.source not in sys.path:
            sys.path.append(self.source)

    def remove_source_from_path(self):
        if self.source in sys.path:
            sys.path.remove(self.source)

    def add_envs(self):
        for k, v in self.envs.items():
            if k in os.environ:
                self._old_envs[k] = os.environ[k]
            os.environ[k] = v

    def remove_envs(self):
        for k in self.envs:
            os.environ.pop(k, None)
        os.environ.update(self._old_envs)

    def __enter__(self):
        self.add_source_to_path()
        self.add_envs()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove_source_from_path()
        self.remove_envs()


import_from_source = ImportFromContext(source=SOURCE, envs={
    'AWS_REGION': 'eu-central-1',
})
