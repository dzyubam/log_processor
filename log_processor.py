import argparse
import re
from datetime import datetime
from enum import Enum
from os.path import isfile
from pprint import pprint as pp

from sqlalchemy import Column, Integer, String, DateTime
from database import Base, db_session

LOGIN_PAGE = 'wp-login.php'


class EventType(Enum):
    # POST to wp-login.php
    post_login = 0
    # GET of wp-login.php
    get_login = 1
    # GET with 4XX status code
    get_4xx = 2
    # POST with 4XX status code
    post_4xx = 3
    # any other POST
    post = 4
    # any other GET
    get = 5


class Event(Base):
    """
    Event extracted from (access) log file
    """
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(100))
    event_type = Column(String(100))
    status_code = Column(Integer)
    user_agent = Column(String(1000))
    url = Column(String(1000))
    date_time = Column(DateTime)
    log_line = Column(String(1000))

    def __init__(self, source_ip, event_type, status_code, user_agent, url, date_time, log_line):
        """
        @param source_ip: Source IPv4 address
        @type source_ip: str
        @param event_type: Type of event
        @type event_type: EventType
        @param status_code: Status code
        @type status_code: int
        @param user_agent: User agent string
        @type user_agent: str
        @param url: URL
        @type url: str
        @param date_time: Datetime value
        @type date_time: datetime
        @param log_line: Parsed log line
        @type log_line: str
        """
        self.source_ip = source_ip
        self.event_type = event_type.name if event_type is not None else None
        self.status_code = status_code
        self.user_agent = user_agent
        self.url = url
        self.date_time = date_time
        self.log_line = log_line

    def __repr__(self):
        """
        String representation
        @rtype: str
        """
        return '<Event {}>'.format(self.__dict__)

    def save(self):
        """
        Persist in DB
        @rtype: Event
        """
        print('.', end='')
        db_session.add(self)
        db_session.commit()
        return self

    @staticmethod
    def save_all(events_to_save):
        """
        Persist all passed Event objects
        @param events_to_save: List of Event objects to save
        @type events_to_save: list[Event]
        @rtype: bool
        """
        if events_to_save:
            print("Saving {} Events".format(len(events_to_save)))
            db_session.add_all(events_to_save)
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


def get_datetime(line):
    """
    Extracts datetime value from string
    @param line:
    @rtype: datetime | None
    """
    date_time = datetime.now()
    form = '%d/%b/%Y:%H:%M:%S %z'
    split_line = line.split('[')
    if len(split_line) > 1:
        split_line = split_line[1].split(']')
        try:
            date_time = datetime.strptime(split_line[0], form)
        except ValueError as e:
            print("Error '{}' parsing string '{}' to datetime using format '{}'".format(e, split_line[0], form))
        except Exception as e:
            print("Error '{}' parsing string '{}' to datetime using format '{}'".format(e, split_line[0], form))

    return date_time


def get_method(line):
    """
    Extracts HTTP method
    @param line:
    @rtype: str
    """
    method = 'NO METHOD FOUND'
    split_line = line.split('"')
    if len(split_line) > 1:
        search_result = re.search(r'^[A-Z]+', split_line[1])
        if search_result:
            method = search_result.group(0)
    return method


def get_source_ip(line):
    """
    Extracts source IPv4 address from line
    @param line: Log line to extract from
    @type line: str
    @rtype: str
    """
    search_result = re.search(r'^\d+.\d+.\d+.\d+', line)
    return search_result.group(0) if search_result else ''


def get_status_code(line):
    """
    Extract status code
    @param line: Log line
    @type line: str
    @rtype: int
    """
    status_code = 999
    split_line = line.split('"')
    if len(split_line) > 1:
        search_result = re.search(r' \d{3} ', split_line[2])
        if search_result:
            status_code = int(search_result.group(0).strip())
    return status_code


def get_url(line):
    """
    Extract page URL
    @param line: Log line
    @type line: str
    @rtype: str
    """
    url = 'NO URL FOUND'
    split_line = line.split('"')
    if len(split_line) > 1:
        search_result = re.search(r' (/[^\s]+)', split_line[1])
        if search_result:
            url = search_result.group(0).strip()
    return url


def get_user_agent(line):
    """
    Extract user agent string
    @param line: Log line
    @type line: str
    @rtype: str
    """
    user_agent = 'NO USER AGENT'
    split_line = line.split('"')
    if len(split_line) > 5:
        user_agent = split_line[5]
    return user_agent


def is_post(line):
    """
    Determine if it was a POST request
    @param line: Log line
    @type line: str
    @rtype: bool
    """
    verb = get_method(line)
    return verb == 'POST'


def is_get(line):
    """
    Determine if it was a GET request
    @param line: Log line
    @type line: str
    @rtype: bool
    """
    verb = get_method(line)
    return verb == 'GET'


def is_login_page(line):
    """
    Determine if it was a login page
    @param line: Log line
    @type line: str
    @rtype: bool
    """
    return LOGIN_PAGE in get_url(line)


def parse_line(line, event_type=None):
    """
    Parse a single line to extract a possible match on event_type
    @param line: A single line to parse
    @type line: str
    @param event_type: EventType we look for
    @type event_type: EventType | None
    @rtype: Event | None
    """
    event = None
    source_ip = get_source_ip(line)
    post = is_post(line)
    get = is_get(line)
    status_code = get_status_code(line)
    user_agent = get_user_agent(line)
    url = get_url(line)
    date_time = get_datetime(line)
    login_page = is_login_page(line)

    if event_type:
        if event_type == EventType.post_login:
            post = is_post(line)
            login_page = is_login_page(line)
            if post and login_page:
                event = Event(source_ip, event_type, status_code, user_agent, url, date_time, line)
    else:
        # TODO: add all event type smarter
        for e in EventType:
            if e == EventType.post_login:
                if post and login_page:
                    event_type = e
                    break
            elif e == EventType.get_login:
                if get and login_page:
                    event_type = e
                    break
            elif e == EventType.post_4xx:
                if post and (400 <= status_code < 500):
                    event_type = e
                    break
            elif e == EventType.get_4xx:
                if get and (400 <= status_code < 500):
                    event_type = e
                    break
            elif e == EventType.post:
                if post:
                    event_type = e
                    break
            elif e == EventType.get:
                if get:
                    event_type = e
                    break
        event = Event(source_ip, event_type, status_code, user_agent, url, date_time, line)

    return event


def parse_file(file_name, event_type=None, save_to_db=False):
    """
    Parse a given file and return list of dicts representing rows that matched a given EventType
    @param file_name: File to parse
    @type file_name: str
    @param event_type: EventType to look for
    @type event_type: EventType | None
    @param save_to_db: Save to DB?
    @type save_to_db: bool
    @rtype: list[Event]
    """
    if not isfile(file_name):
        raise ValueError("Cannot find file '{}'".format(file_name))

    result = list()

    with open(file_name, "r") as f:
        for line in f:
            parsed_event = parse_line(line, event_type)
            if parsed_event:
                result.append(parsed_event)

    if save_to_db:
        Event.save_all(result)

    return result


if __name__ == '__main__':
    # TODO: add option to parse multiple files by giving a file mask
    # what parameters should it accept? file, action, event_type, etc
    parser = argparse.ArgumentParser(description='Parse a log file and output results')
    parser.add_argument('--file', '-f', help='File to parse or file mask to parse many files', type=str, required=True)
    parser.add_argument('--event', '-e', help='Event type to look for', type=int, required=False)
    parser.add_argument('--persist', '-s', help='Save to DB', type=bool, required=False)
    parser.add_argument('--print', '-p', help='Print output', type=bool, required=False)
    args = parser.parse_args()
    print(args.__dict__)
    parsed_event_type = EventType(args.event) if args.event else None
    save_to_dp = True if args.persist else False
    print_results = True if args.print else False
    events = parse_file(args.file, parsed_event_type, save_to_dp)
    if args.print:
        pp(sorted(events, key=lambda e: (len(e.source_ip), e.source_ip)))
    print('Number of events', len(events))
