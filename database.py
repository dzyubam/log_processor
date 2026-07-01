from pathlib import Path
import os

# Set env vars BEFORE importing sqlalchemy to control engine creation
os.environ.setdefault(
    "PROCESSOR_DB_FILE", str(Path(__file__).resolve().parent / "log_processor.db")
)
os.environ.setdefault(
    "REPORT_DB_FILE", str(Path(__file__).resolve().parent / "log_report.db")
)

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm import declarative_base

PROCESSOR_DB_FILE = os.environ["PROCESSOR_DB_FILE"]
REPORT_DB_FILE = os.environ["REPORT_DB_FILE"]

processor_engine = create_engine("sqlite:///{}".format(PROCESSOR_DB_FILE))
report_engine = create_engine("sqlite:///{}".format(REPORT_DB_FILE))

_proc_sessionmaker = sessionmaker(
    autocommit=False, autoflush=False, bind=processor_engine
)
_report_sessionmaker = sessionmaker(
    autocommit=False, autoflush=False, bind=report_engine
)

processor_db_session = scoped_session(_proc_sessionmaker)
report_db_session = scoped_session(_report_sessionmaker)

BaseProcessor = declarative_base()
BaseProcessor.query = processor_db_session.query_property()
BaseReport = declarative_base()
BaseReport.query = report_db_session.query_property()


def _rebind(new_processor_path, new_report_path):
    global processor_engine, report_engine

    processor_engine.dispose()
    report_engine.dispose()

    processor_engine = create_engine("sqlite:///{}".format(new_processor_path))
    report_engine = create_engine("sqlite:///{}".format(new_report_path))

    _proc_sessionmaker.configure(bind=processor_engine)
    _report_sessionmaker.configure(bind=report_engine)


def init_db():
    env_p = os.environ.get("PROCESSOR_DB_FILE")
    env_r = os.environ.get("REPORT_DB_FILE")

    default_p = str(Path(__file__).resolve().parent / "log_processor.db")
    default_r = str(Path(__file__).resolve().parent / "log_report.db")

    if env_p != default_p or env_r != default_r:
        _rebind(env_p, env_r)

    BaseProcessor.metadata.create_all(bind=processor_engine)
    BaseReport.metadata.create_all(bind=report_engine)
