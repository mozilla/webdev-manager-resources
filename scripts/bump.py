#!/usr/bin/env python
import json
import os
import sys
import urllib

import requests

# A script that bumps all bugs in a given target milestone on to the
# next target milestone. If only the first milestone is specified, it does
# a dry run, printing out the bugs that would normally be moved. With both
# milestones specified it moves the bugs between the two. For example:
#
# ./bump.py 2013-10-29 2013-11-05
#
# The config (~/.bugzilla) needs to look like this.
#
# {
#    "auth": [
#        "amckay@mozilla.com",
#        "*****"
#    ],
#    "bump": {
#        "product": "Marketplace",
#        "component": "Payments/Refunds",
#        "bug_status": ["UNCONFIRMED", "ASSIGNED", "REOPENED", "NEW"]
#    }
# }

config_file = open(os.path.expanduser('~/.bugzilla'), 'r')
config = json.load(config_file)

root = 'https://api-dev.bugzilla.mozilla.org/latest/'

GREEN = "\033[1m\033[92m"
RED = '\033[1m\033[91m'
RESET = "\x1B[m"


def call(method, url, params):
    mthd = getattr(requests, method)
    user = {'username': config['auth'][0], 'password': config['auth'][1]}
    if method in ['patch', 'put']:
        full_url = '%sbug/%s?%s' % (root, url,
                                    urllib.urlencode(user, doseq=True))
        return mthd(full_url, data=json.dumps(params))

    params.update(user)
    full_url = '%sbug/%s?%s' % (root, url,
                                urllib.urlencode(params, doseq=True))
    return mthd(full_url)


def bump(source, dest):
    args = config['bump']
    args['target_milestone'] = source
    bugs = call('get', '', args)

    for bug in bugs.json()['bugs']:
        print '%s%s%s: %s (%s)' % (
            GREEN, bug['id'], RESET,
            bug['assigned_to']['real_name'], bug['summary']
        )
        bug = call('get', bug['id'], {}).json()
        if dest:
            bug['target_milestone'] = dest
            res = call('put', bug['id'], bug)
            if res.status_code == 202:
                print '%sBug updated%s' % (GREEN, RESET)
            else:
                print '%sFailure on update:%s\nStatus:%s, Message:%s' % (
                    RED, RESET, res.status_code, res.content)

    print 'No dest specified, %sskipped%s' % (RED, RESET)


if __name__ == '__main__':
    start = sys.argv[1]
    try:
        end = sys.argv[2]
    except IndexError:
        end = None
    bump(start, end)
