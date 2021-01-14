#!/usr/bin/python3
# encoding: utf-8
'''
check gerrit for certain files in mw core being touched by recent
commits, as long as I'm not owner or reviewer

I wouldn't do this but reviewerbot seems to have not worked in
a recent instance and that's really problematic
'''
import json
import sys
import requests


# https://gerrit.wikimedia.org/r/changes/?q=-age:7d+-owner:ariel@wikimedia.org
#    +-reviewer:ariel@wikimedia.org+project:mediawiki/core
#    +branch:master+path:^maintenance%2Fdump.*&n=25
BASEURL = "https://gerrit.wikimedia.org/r/changes/"
# could add -status:abandoned  later on
QPARAMS = ['-owner:ariel@wikimedia.org', '-reviewer:ariel@wikimedia.org',
           'project:mediawiki/core', 'branch:master']
# number of changes to get in a single request. we should no way reach this number
MAXCHANGES = '25'
PATHS = ["^maintenance/dump.*", "^maintenance%2Fincludes%2F.*Dump.*"]
USERAGENT = "gerrit_check.py/0.1 (atg)"


def usage(message=None):
    '''display usage info about this script'''
    if message is not None:
        print(message)
    usage_message = """Usage: gerrit_check.py <days>| --help

Arguments:

  <days> only check commits newer than this
         default: 7
  --help    (-h):   display this usage message
"""
    print(usage_message)
    sys.exit(1)


def display_changes(change_lists):
    '''
    grab commit id and commit first line and display them,
    that's all we care about
    I could make gerrit do more work to give me the actual
    file names modified but really, who cares
    '''
    for change_list in change_lists:
        if change_list:
            for change in change_list:
                print("Change:", change['change_id'], change['subject'])


def get_changes(days):
    '''
    get a list of gerrit changs of the sort we want, for the
    last n days. this includes changesets created or updated
    in the last n days.
    '''
    result_sets = []
    for path in PATHS:
        q_params = QPARAMS[:]
        other_params = ['-age:' + str(days) + "d", 'path:' + path]
        q_params.extend(other_params)
        paramstring = "+".join(q_params)
        params = "q={paramstring}&n={num}".format(paramstring=paramstring, num=MAXCHANGES)
        url = BASEURL + "?" + params
        response = requests.get(url, headers={'User-Agent': USERAGENT})
        # print(response.url)
        if response.status_code == 200:
            if response.text:
                results = json.loads(response.text[5:])
                result_sets.append(results)
        else:
            print("response status code is", response.status_code)

    return result_sets


def do_main():
    '''
    entry point
    '''
    days = 7

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        usage()

    if len(sys.argv) > 1:
        if not sys.argv[1].isdigit():
            usage("the sole argument to this script must be the number of days")
        days = int(sys.argv[1])

    changes_json = get_changes(days)
    display_changes(changes_json)


if __name__ == '__main__':
    do_main()
