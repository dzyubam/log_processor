import pytest
import random
from datetime import datetime
from os.path import isfile


from log_processor import (
    get_source_ip,
    get_method,
    get_url,
    is_post,
    is_login_page,
    get_status_code,
    get_user_agent,
    get_datetime,
    parse_line,
    Event,
    EventType,
)
from report import (
    Report,
    get_base_reports,
    get_counts_by_event_type,
    generate_reports,
    delete_all_reports,
)
from database import init_db, PROCESSOR_DB_FILE, REPORT_DB_FILE


@pytest.fixture(autouse=True)
def setup():
    init_db()


def test_get_source_ip():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_source_ip(line)
    assert isinstance(result, str)
    assert "150.95.105.63" == result

    line = (
        '0.0.0.0 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_source_ip(line)
    assert "0.0.0.0" == result

    line = (
        '- - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_source_ip(line)
    assert "" == result

    line = (
        '- - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0 150.95.105.63 xxx"'
    )
    result = get_source_ip(line)
    assert "" == result


def test_get_method():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert isinstance(result, str)
    assert "GET" == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert "POST" == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "PUT /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert "PUT" == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "DELETE /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert "DELETE" == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "HEAD /backup.zip HTTP/1.1" 404 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert "HEAD" == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "OPTIONS /backup.zip HTTP/1.1" 404 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert "OPTIONS" == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "no_method /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_method(line)
    assert "NO METHOD FOUND" == result


def test_get_url():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_url(line)
    assert isinstance(result, str)
    assert "/wp-login.php" == result

    line = (
        '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET /wp-content/uploads/2007/09/map.gif HTTP/1.1" '
        '200 7930 "-" "Googlebot-Image/1.0"'
    )
    result = get_url(line)
    assert "/wp-content/uploads/2007/09/map.gif" == result

    line = (
        '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET / HTTP/1.1" '
        '200 7930 "-" "Googlebot-Image/1.0"'
    )
    result = get_url(line)
    assert "/" == result

    line = (
        '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET \x03 HTTP/1.1" '
        '200 7930 "-" "Googlebot-Image/1.0"'
    )
    result = get_url(line)
    assert "NO URL FOUND" == result


def test_is_post():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    assert is_post(line)
    assert is_login_page(line)

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    assert not is_post(line)
    assert is_login_page(line)

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "PUT /wp-admin/wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    assert not is_post(line)
    assert is_login_page(line)


def test_get_status_code():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_status_code(line)
    assert 200 == result

    line = (
        '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET \x03 HTTP/1.1" '
        '200 7930 "-" "Googlebot-Image/1.0"'
    )
    result = get_status_code(line)
    assert 200 == result

    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 404 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_status_code(line)
    assert 404 == result

    # No status code found
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_status_code(line)
    assert 999 == result


def test_get_user_agent():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_user_agent(line)
    assert (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
        == result
    )

    line = (
        '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET \x03 HTTP/1.1" '
        '200 7930 "-" "Googlebot-Image/1.0"'
    )
    result = get_user_agent(line)
    assert "Googlebot-Image/1.0" == result

    line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 5536 "-"'
    result = get_user_agent(line)
    assert "NO USER AGENT" == result


def test_get_datetime():
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_datetime(line)
    assert result is not None
    assert isinstance(result, datetime)
    assert 1 == result.day
    assert 10 == result.month
    assert 2019 == result.year
    assert 7 == result.hour
    assert 26 == result.minute
    assert 54 == result.second
    assert "UTC+03:00" == result.tzname()

    line = (
        '150.95.105.63 - - [18/Oct/2019:21:41:07 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = get_datetime(line)
    assert result is not None
    assert isinstance(result, datetime)
    assert 18 == result.day
    assert 10 == result.month
    assert 2019 == result.year
    assert 21 == result.hour
    assert 41 == result.minute
    assert 7 == result.second
    assert "UTC+03:00" == result.tzname()


def test_init_db():
    assert isfile(PROCESSOR_DB_FILE)
    assert isfile(REPORT_DB_FILE)
    # Check that tables are created
    Event.query.first()
    Report.query.first()


def test_parse_line():
    # post_login
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = parse_line(line)
    assert isinstance(result, Event)
    assert "150.95.105.63" == result.source_ip
    assert "post_login" == result.event_type
    assert 200 == result.status_code
    assert (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
        == result.user_agent
    )
    assert "/wp-login.php" == result.url
    expected_datetime = datetime(2019, 10, 1, 7, 26, 54)
    assert expected_datetime.year == result.date_time.year
    assert expected_datetime.month == result.date_time.month
    assert expected_datetime.day == result.date_time.day
    assert expected_datetime.hour == result.date_time.hour
    assert expected_datetime.minute == result.date_time.minute
    assert expected_datetime.second == result.date_time.second

    # get_login
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /wp-login.php HTTP/1.1" 200 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = parse_line(line)
    assert isinstance(result, Event)
    assert "get_login" == result.event_type

    # post_4xx
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /hello.php HTTP/1.1" 404 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = parse_line(line)
    assert isinstance(result, Event)
    assert "post_4xx" == result.event_type
    assert 404 == result.status_code

    # get_4xx
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /hello.php HTTP/1.1" 401 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = parse_line(line)
    assert isinstance(result, Event)
    assert "get_4xx" == result.event_type
    assert 401 == result.status_code

    # post
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /index.php HTTP/1.1" 301 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = parse_line(line)
    assert isinstance(result, Event)
    assert "post" == result.event_type
    assert 301 == result.status_code

    # get
    line = (
        '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /index.php HTTP/1.1" 302 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    result = parse_line(line)
    assert isinstance(result, Event)
    assert "get" == result.event_type
    assert 302 == result.status_code


# @pytest.mark.skip
def test_event_query_all():
    line = (
        'xxx.xx.xxx.xx - - [01/Oct/2019:07:26:54 +0300] "GET /index.php HTTP/1.1" 302 5536 "-" '
        '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
    )
    test_event = parse_line(line)
    # Save
    test_event.save()
    results = Event.query.all()
    assert isinstance(results, list)
    assert test_event in results

    # Delete
    test_event.delete()
    results = Event.query.all()
    assert isinstance(results, list)
    assert test_event not in results

    print(len(results), "results found")


def test_get_base_reports():
    reports = get_base_reports()
    assert isinstance(reports, dict)
    if reports:
        for r in reports.values():
            assert isinstance(r, Report)
    else:
        print("No reports generated! Is database empty?")


# @pytest.mark.skip
def test_get_counts_by_event_type():
    for event_type in EventType:
        print()
        print(event_type)
        counts = get_counts_by_event_type(event_type)
        assert isinstance(counts, dict)
        assert 0 < len(counts)
        all_items = list(counts.items())
        print("Total items: {}".format(len(all_items)))
        print()
        # Shuffle to test different items every time
        random.shuffle(all_items)
        for i, (ip, count) in enumerate(all_items):
            if i < 10:
                assert isinstance(count, int)
                assert isinstance(ip, str)
                assert (
                    count
                    == Event.query.filter(
                        Event.event_type == event_type.name, Event.source_ip == ip
                    ).count()
                )
                print("'{}'".format(ip), count)


def test_generate_reports():
    existing_reports_with_comments = Report.query.filter(Report.comment != "").all()
    full_reports = generate_reports()
    assert isinstance(full_reports, dict)
    newly_generated_reports_with_comments = 0
    for report in full_reports.values():
        assert isinstance(report, Report)
        if report.comment:
            newly_generated_reports_with_comments += 1
    # Check that reports that had comments still have them
    assert len(existing_reports_with_comments) == newly_generated_reports_with_comments
    print("Generated {} reports".format(len(full_reports)))
    delete_all_reports()
    Report.save_all(full_reports.values())
    print("Saved {} reports".format(len(full_reports)))


def test_get_comment_for_ip():
    reports_with_comments = Report.query.filter(Report.comment != "").all()
    for r in reports_with_comments:
        assert r.comment == Report.get_by_ip(r.source_ip).comment
