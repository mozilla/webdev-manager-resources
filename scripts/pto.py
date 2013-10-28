#!/usr/bin/env python
import json
import os
import sys
import urllib
from datetime import date, datetime, timedelta

import requests

# Ths config file needs to look like this and contains your LDAP credentials.
# Sigh.
#
# {
#    "auth": [
#        "amckay@mozilla.com",
#        "**********"
#    ],
#    "users": [
#        "Kumar McMillan",
#        "Stuart Colville"
#     ]
# }
config_file = os.path.expanduser('~/.pto')
config = json.load(open(config_file, 'r'))

base_url = 'https://intranet.mozilla.org/pto/export.php'
in_date_fmt = '%m/%d/%Y'
out_date_fmt = '%Y-%m-%d'  # Consistency, yay!

GREEN = '\033[1m\033[92m'
CYAN = '\033[1m\033[36m'
RESET = '\x1B[m'


def get(config, start, end):
    args = {'start_date_from': start.strftime(in_date_fmt),
            'start_date_to': end.strftime(in_date_fmt),
            'end_date_from': start.strftime(in_date_fmt),
            'end_date_to': end.strftime(in_date_fmt),
            'user': config['auth'][0],
            'format': 'json'}
    for user in config['users']:
        first, last = user.rsplit(' ', 1)
        args['first_name'] = first
        args['last_name'] = last
        url = '%s?%s' % (base_url, urllib.urlencode(args))
        res = requests.get(url, auth=tuple(config['auth']))

        if not res.status_code == 200:
            print 'HTTP Response: %s, skipping' % res.status_code
            continue

        result = res.json()
        for row in result['aaData']:  # Whatever aaData is.
            start, end = (datetime.strptime(row[6], out_date_fmt),
                          datetime.strptime(row[7], out_date_fmt))
            if start != end:
                print '%s%s%s: %s (%s) to %s (%s)' % (
                    GREEN, user, RESET, start.strftime('%A'),
                    start.strftime(out_date_fmt), end.strftime('%A'),
                    end.strftime(out_date_fmt))
            else:
                print '%s%s%s: %s (%s)' % (
                    GREEN, user, RESET, start.strftime('%A'),
                    start.strftime(out_date_fmt))

        if not result['aaData']:
            print 'No PTO for %s%s%s.' % (CYAN, user, RESET)


if __name__ == '__main__':
    try:
        week = sys.argv[1]
    except IndexError:
        week = None

    today = date.today()
    if week not in ['this', 'next']:
        print 'Assuming next week.'
        week = 'next'

    if week == 'next':
        today += timedelta(days=7)

    start = today - timedelta(days=today.isoweekday())
    end = start + timedelta(days=6)
    get(config, start, end)
