"""共享 fixtures。"""

import pytest

from src.demo_data import seed
from src.config import Config
from src.repository.sqlite import SQLiteRepository
from src.service import LeakDetectionService

DT = "2026-03-05"


@pytest.fixture()
def repo():
    r = SQLiteRepository(":memory:")
    seed(r)
    return r


@pytest.fixture()
def config():
    return Config()


@pytest.fixture()
def service(repo, config):
    return LeakDetectionService(repo, config)
