from database import db_session, Base
from log_processor import Event, EventType

from sqlalchemy import Column, Integer, String, DateTime, func, Text


class Report(Base):
    """
    Report generated for IP address from log_processor DB
    """
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(100))
    latest = Column(DateTime)
    total_count = Column(Integer)
    post_login_count = Column(Integer)
    get_login_count = Column(Integer)
    get_4xx_count = Column(Integer)
    post_4xx_count = Column(Integer)
    post_count = Column(Integer)
    get_count = Column(Integer)
    head_count = Column(Integer)
    options_count = Column(Integer)
    comment = Column(Text)

    def __init__(self, source_ip, latest, total_count, post_login_count=0, get_login_count=0, get_4xx_count=0,
                 post_4xx_count=0, post_count=0, get_count=0, head_count=0, options_count=0, comment=''):
        """
        @param source_ip: Source IPv4 address
        @type source_ip: str
        @param latest: Datetime of latest request
        @type latest: datetime
        @param total_count: Total number of requests
        @type total_count: int
        @param post_login_count: Total number of POST requests to login page
        @type post_login_count: int
        @param get_login_count: Total number of GET requests to login page
        @type get_login_count: int
        @param get_4xx_count: Total number of GET requests with 4XX result code
        @type get_4xx_count: int
        @param post_4xx_count: Total number of POST requests with 4XX result code
        @type post_4xx_count: int
        @param post_count: Total number of POST requests
        @type post_count: int
        @param get_count: Total number of GET requests
        @type get_count: int
        @param head_count: Total number of HEAD requests
        @type head_count: int
        @param options_count: Total number of OPTIONS requests
        @type options_count: int
        @param comment: Comment about IP address
        @type comment: str
        """
        self.source_ip = source_ip
        self.latest = latest
        self.total_count = total_count
        self.post_login_count = post_login_count
        self.get_login_count = get_login_count
        self.get_4xx_count = get_4xx_count
        self.post_4xx_count = post_4xx_count
        self.post_count = post_count
        self.get_count = get_count
        self.head_count = head_count
        self.options_count = options_count
        self.comment = comment

    def __repr__(self):
        """
        String representation
        @rtype: str
        """
        return '<{} {}>'.format(self.__class__.__name__, self.__dict__)

    def save(self):
        """
        Persist in DB
        @rtype: Report
        """
        db_session.add(self)
        db_session.commit()
        return self

    @staticmethod
    def save_all(reports_to_save):
        """
        Persist all passed objects
        @param reports_to_save: List of Report objects to save
        @type reports_to_save: list[Report]
        @rtype: bool
        """
        if reports_to_save:
            db_session.add_all(reports_to_save)
            db_session.commit()
            return True
        else:
            return False

    def delete(self):
        """
        Delete object from DB
        @rtype: bool
        """
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            print("Error '{}' when deleting {}".format(e, self))
            return False
        return True


def get_base_reports():
    """
    Generate reports with IP, total count and latest request date
    @rtype: list[Report]
    """
    reports = list()
    grouped_events = db_session.query(Event.source_ip,
                                      func.max(Event.date_time),
                                      func.count(Event.source_ip)).group_by(Event.source_ip).all()
    for g in grouped_events:
        reports.append(Report(g[0], g[1], g[2]))
    return reports


def get_counts_by_event_type(event_type):
    """
    Generate updates for all IPs for a given EventType
    @param event_type: EventType to generate report for
    @type event_type: EventType
    @return: Dict with IP as key and count as value
    @rtype: dict
    """
    counts = dict()
    grouped_events = db_session.query(Event.source_ip, func.count(Event.source_ip)).group_by(Event.source_ip).filter(
         Event.event_type == event_type.name).all()
    for e in grouped_events:
        counts[e[0]] = e[1]
    return counts
