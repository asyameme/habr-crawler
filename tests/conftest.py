import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('MAX_DEPTH', '2')
os.environ.setdefault('HABR_RATE_LIMIT_SEC', '10')
os.environ.setdefault('DEFAULT_TIMEOUT', '30')
os.environ.setdefault('MAX_PAGES', '1000')

from models import Base  # noqa: E402


@pytest.fixture()
def engine():
    engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def session(engine):
    with Session(engine) as session:
        yield session
        session.rollback()
