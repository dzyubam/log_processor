# Description
Parses Apache2 access logs and saves rows in sqlite3 DB for further reporting and processing

# Why?
This is a simple tool meant to be executed manually or as a cron job on a web server and extracting requests from Apache2 access log.

# Example usage

## Options
- `-f <file>`: Path to Apache2 access log file or glob pattern (e.g., `/var/log/apache2/access.log.*`)
- `-p`: Print extracted requests to console
- `-s`: Save to SQLite database (`log_processor.db`)

## Print extracted requests:

## Print extracted requests:

$ python3 log_processor.py -f "/var/log/apache2/access.log.1" -p 1

## Save extracted requests in sqlite3 database:

$ python3 log_processor.py -f "/var/log/apache2/access.log.1" -s 1

## Do the same with multiple files matching a given mask:

$ python3 log_processor.py -f "/var/log/apache2/access.log.*" -s 1
