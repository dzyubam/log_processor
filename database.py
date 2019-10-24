from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_FILE = '/home/dzyubam/tmp/log_processor.db'


engine = create_engine('sqlite:///{}'.format(DB_FILE), convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # from log_processor import Event
    Base.metadata.create_all(bind=engine)
