from datetime import datetime
from unittest import TestCase
from os.path import isfile


from log_processor import get_source_ip, get_method, get_url, is_post, is_login_page, get_status_code, get_user_agent, \
    get_datetime, parse_line, Event
from report import Report, get_base_reports
from database import init_db, DB_FILE


class TestLogProcessor(TestCase):
    def test_get_source_ip(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_source_ip(line)
        self.assertIsInstance(result, str)
        self.assertEqual('150.95.105.63', result)

        line = '0.0.0.0 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_source_ip(line)
        self.assertEqual(result, '0.0.0.0')

        line = '- - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_source_ip(line)
        self.assertEqual(result, '')

        line = '- - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0 150.95.105.63 xxx"'
        result = get_source_ip(line)
        self.assertEqual(result, '')

    def test_get_method(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertIsInstance(result, str)
        self.assertEqual('GET', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertEqual('POST', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "PUT /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertEqual('PUT', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "DELETE /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertEqual('DELETE', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "HEAD /backup.zip HTTP/1.1" 404 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertEqual('HEAD', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "OPTIONS /backup.zip HTTP/1.1" 404 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertEqual('OPTIONS', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "no_method /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_method(line)
        self.assertEqual('NO METHOD FOUND', result)

    def test_get_url(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:52 +0300] "GET /wp-login.php HTTP/1.1" 200 5128 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_url(line)
        self.assertIsInstance(result, str)
        self.assertEqual('/wp-login.php', result)

        line = '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET /wp-content/uploads/2007/09/map.gif HTTP/1.1" ' \
               '200 7930 "-" "Googlebot-Image/1.0"'
        result = get_url(line)
        self.assertEqual('/wp-content/uploads/2007/09/map.gif', result)

        line = '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET / HTTP/1.1" ' \
               '200 7930 "-" "Googlebot-Image/1.0"'
        result = get_url(line)
        self.assertEqual('/', result)

        line = '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET \x03 HTTP/1.1" ' \
               '200 7930 "-" "Googlebot-Image/1.0"'
        result = get_url(line)
        self.assertEqual('NO URL FOUND', result)

    def test_is_post(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        self.assertTrue(is_post(line))
        self.assertTrue(is_login_page(line))

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        self.assertFalse(is_post(line))
        self.assertTrue(is_login_page(line))

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "PUT /wp-admin/wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        self.assertFalse(is_post(line))
        self.assertTrue(is_login_page(line))

    def test_get_status_code(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_status_code(line)
        self.assertEqual(200, result)

        line = '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET \x03 HTTP/1.1" ' \
               '200 7930 "-" "Googlebot-Image/1.0"'
        result = get_status_code(line)
        self.assertEqual(200, result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 404 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_status_code(line)
        self.assertEqual(404, result)

        # No status code found
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_status_code(line)
        self.assertEqual(999, result)

    def test_get_user_agent(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_user_agent(line)
        self.assertEqual('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0', result)

        line = '66.249.79.159 - - [01/Oct/2019:07:02:14 +0300] "GET \x03 HTTP/1.1" ' \
               '200 7930 "-" "Googlebot-Image/1.0"'
        result = get_user_agent(line)
        self.assertEqual('Googlebot-Image/1.0', result)

        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 5536 "-"'
        result = get_user_agent(line)
        self.assertEqual('NO USER AGENT', result)

    def test_get_datetime(self):
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_datetime(line)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, datetime)
        self.assertEqual(1, result.day)
        self.assertEqual(10, result.month)
        self.assertEqual(2019, result.year)
        self.assertEqual(7, result.hour)
        self.assertEqual(26, result.minute)
        self.assertEqual(54, result.second)
        self.assertEqual('UTC+03:00', result.tzname())

        line = '150.95.105.63 - - [18/Oct/2019:21:41:07 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = get_datetime(line)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, datetime)
        self.assertEqual(18, result.day)
        self.assertEqual(10, result.month)
        self.assertEqual(2019, result.year)
        self.assertEqual(21, result.hour)
        self.assertEqual(41, result.minute)
        self.assertEqual(7, result.second)
        self.assertEqual('UTC+03:00', result.tzname())

    def test_init_db(self):
        init_db()
        self.assertTrue(isfile(DB_FILE))
        # Check that tables are created
        Event.query.first()
        Report.query.first()

    def test_parse_line(self):
        # post_login
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = parse_line(line)
        self.assertIsInstance(result, Event)
        self.assertEqual('150.95.105.63', result.source_ip)
        self.assertEqual('post_login', result.event_type)
        self.assertEqual(200, result.status_code)
        self.assertEqual('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0',
                         result.user_agent)
        self.assertEqual('/wp-login.php', result.url)
        expected_datetime = datetime(2019, 10, 1, 7, 26, 54)
        self.assertEqual(expected_datetime.year, result.date_time.year)
        self.assertEqual(expected_datetime.month, result.date_time.month)
        self.assertEqual(expected_datetime.day, result.date_time.day)
        self.assertEqual(expected_datetime.hour, result.date_time.hour)
        self.assertEqual(expected_datetime.minute, result.date_time.minute)
        self.assertEqual(expected_datetime.second, result.date_time.second)

        # get_login
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /wp-login.php HTTP/1.1" 200 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = parse_line(line)
        self.assertIsInstance(result, Event)
        self.assertEqual('get_login', result.event_type)

        # post_4xx
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /hello.php HTTP/1.1" 404 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = parse_line(line)
        self.assertIsInstance(result, Event)
        self.assertEqual('post_4xx', result.event_type)
        self.assertEqual(404, result.status_code)

        # get_4xx
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /hello.php HTTP/1.1" 401 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = parse_line(line)
        self.assertIsInstance(result, Event)
        self.assertEqual('get_4xx', result.event_type)
        self.assertEqual(401, result.status_code)

        # post
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "POST /index.php HTTP/1.1" 301 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = parse_line(line)
        self.assertIsInstance(result, Event)
        self.assertEqual('post', result.event_type)
        self.assertEqual(301, result.status_code)

        # get
        line = '150.95.105.63 - - [01/Oct/2019:07:26:54 +0300] "GET /index.php HTTP/1.1" 302 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        result = parse_line(line)
        self.assertIsInstance(result, Event)
        self.assertEqual('get', result.event_type)
        self.assertEqual(302, result.status_code)

    def test_event_query_all(self):
        line = 'xxx.xx.xxx.xx - - [01/Oct/2019:07:26:54 +0300] "GET /index.php HTTP/1.1" 302 5536 "-" ' \
               '"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"'
        test_event = parse_line(line)
        # Save
        test_event.save()
        results = Event.query.all()
        self.assertIsInstance(results, list)
        self.assertIn(test_event, results)

        # Delete
        test_event.delete()
        results = Event.query.all()
        self.assertIsInstance(results, list)
        self.assertNotIn(test_event, results)

        print(len(results), 'results found')

    def test_get_base_reports(self):
        reports = get_base_reports()
        self.assertIsInstance(reports, list)
        if reports:
            for r in reports:
                self.assertIsInstance(r, Report)
            Report.save_all(reports)
            self.assertIsInstance(Report.query.first(), Report)
