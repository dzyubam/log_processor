from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

path_to_db = Path(__file__).resolve().parent
PROCESSOR_DB_FILE = '{}/log_processor.db'.format(path_to_db)
REPORT_DB_FILE = '{}/log_report.db'.format(path_to_db)

processor_engine = create_engine('sqlite:///{}'.format(PROCESSOR_DB_FILE), convert_unicode=True)
report_engine = create_engine('sqlite:///{}'.format(REPORT_DB_FILE), convert_unicode=True)
processor_db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=processor_engine))
report_db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=report_engine))

BaseProcessor = declarative_base()
BaseProcessor.query = processor_db_session.query_property()
BaseReport = declarative_base()
BaseReport.query = report_db_session.query_property()


def init_db():
    # Create needed tables
    BaseProcessor.metadata.create_all(bind=processor_engine)
    BaseReport.metadata.create_all(bind=report_engine)
