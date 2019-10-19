#!/usr/bin/python3
# encoding: utf-8
'''
Get mediainfo entry for an uploaded image

This is intended to be run against a wiki that has the MediaInfo extension
enabled, such as commons.wikimedia.org.

Currently MediaInfo items are wikibase entities of type 'item' that are
stored in the 'mediainfo' slot of a revision rather than in wikibase
tables.

MediaInfo items have identifiers of the form Mxxx rather than Qxxx or Pxxx.
This script relies on the fact that currently the Mxxx id is derived from
the page id of the uploaded image. THIS MAY CHANGE and will be broken in
some cases, see
https://phabricator.wikimedia.org/T232087
'''
import getopt
import sys
import requests


def validate_args(args):
    '''
    check that args are valid, not missing, etc.
    and do any necessary arg conversions too
    '''
    if 'title' not in args or args['title'] is None:
        usage("mandatory '--title' argument is missing")
    if 'wiki' not in args or args['wiki'] is None:
        usage("mandatory '--wiki' argument is missing")
    if 'agent' not in args or args['agent'] is None:
        usage("mandatory '--agent' argument is missing")


def get_arg(opt, val, args):
    '''set one arg from opt/val'''
    if opt in ["-t", "--title"]:
        args['title'] = val
    elif opt in ["-w", "--wiki"]:
        args['wiki'] = val
    elif opt in ["-a", "--agent"]:
        args['agent'] = val
    else:
        return False

    return True


def get_flag(opt, args):
    '''set one flag from opt'''
    if opt in ["-v", "--verbose"]:
        args['verbose'] = True
    elif opt in ["-h", "--help"]:
        usage('Help for this script\n')
    else:
        return False
    return True


def parse_args():
    '''get args passed on the command line
    and return as a dict'''
    args = {'title': None,
            'wiki': None,
            'agent': None,
            'verbose': False,
            'help': False}

    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "a:l:t:w:vh", [
                "agent=", "title=", "wiki=", "verbose", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    for (opt, val) in options:
        if not get_arg(opt, val, args) and not get_flag(opt, args):
            usage("Unknown option specified: <%s>" % opt)

    if remainder:
        usage("Unknown option(s) specified: {opt}".format(opt=remainder[0]))

    validate_args(args)
    return args


def usage(message=None):
    '''display usage info about this script'''
    if message is not None:
        print(message)
    usage_message = """Usage: get_mediainfo.py --title <title> --wiki <hostname>
  --agent <user agent> [--verbose]| --help

Arguments:

  --title   (-t):   title of image
  --wiki    (-w):   hostname of the wiki, for viewing web pages and so on
  --agent   (-a):   user agent string for web requests
  --verbose (-v):   display messages about files as they are created
                    default: false
  --help    (-h):   display this usage message

Example uses:
   python3 get_mediainfo.py -t 'Straßenbahn Haltestelle Freizeit- und Erholungszentrum-3.jpg'
                            -w commons.wikimedia.org -a 'get_mediainfo.py/0.1 <your email addy here>'
   python3 get_mediainfo.py -t 'File:Marionina_welchi_(YPM_IZ_072302).jpeg' -v
                            -w commons.wikimedia.org -a 'get_mediainfo.py/0.1 <your email addy here>'
"""
    print(usage_message)
    sys.exit(1)


def get_mediainfo_id(args):
    '''given info for an image, find the mediainfo id for the image
    on the specified wiki'''
    if args['title'].startswith('File:'):
        title = args['title']
    else:
        title = 'File:' + args['title']
    title = title.replace(' ', '_')
    params = {'action': 'query',
              'prop': 'info',
              'titles': title,
              'format': 'json'}
    url = 'https://' + args['wiki'] + '/w/api.php'
    response = requests.post(url, data=params,
                             headers={'User-Agent': args['agent']})
    if args['verbose']:
        print("response:", response.text)
    success = False
    if response.status_code == 200:
        results = response.json()
        if 'query' in results:
            if list(results['query']['pages'].keys()):
                success = True
    if not success:
        sys.stderr.write(response.text + "\n")
        sys.exit(1)
    if args['verbose']:
        print("mediainfo id for page:", 'M' + list(response.json()['query']['pages'].keys())[0])
    return 'M' + list(response.json()['query']['pages'].keys())[0]


def display_mediainfo_info(mediainfo_id, args):
    '''given a mediainfo item id, get whatever info exists about it and display that'''
    params = {'action': 'wbgetentities',
              'ids': mediainfo_id,
              'format': 'json'}
    url = 'https://' + args['wiki'] + '/w/api.php'
    response = requests.post(url, data=params,
                             headers={'User-Agent': args['agent']})
    if args['verbose']:
        print("response:", response.text)
    success = False
    if response.status_code == 200:
        results = response.json()
        if 'entities' in results:
            if mediainfo_id in results['entities']:
                success = True
    if not success:
        sys.stderr.write(response.text + "\n")
        sys.exit(1)
    print("response for id", mediainfo_id + ":")
    print(results['entities'][mediainfo_id])


def do_main():
    '''
    entry point
    '''
    args = parse_args()
    mid = get_mediainfo_id(args)
    display_mediainfo_info(mid, args)


if __name__ == '__main__':
    do_main()
