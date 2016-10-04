"""
  show a count of number of File pages with the WLM greece category,
  and a count of the number of distinct users that uploaded those
  files

  NOTE!!

  this script assumes that the most recent revision of each File
  page was added by the uploader. if a bunch of well meaning
  admins or wlm greece folks come through and edit them all
  then this script will be useless :-P
"""
import sys
import re
import httplib
import time
import json


def handle_http_errors(http_conn, http_result, verbose):
    if http_result.status == 503:
        contents = http_result.read()
        http_conn.close()
        if contents.find("seconds lagged"):
            if verbose >= 1:
                sys.stderr.write(contents)
            lagged = True
            return lagged, contents
    sys.stderr.write("status %s, reason %s\n" %(http_result.status, http_result.reason))
    raise httplib.HTTPException


def get_user_agent():
    return "get_cat_contributors.py/0.1"


def send_request(http_conn, url):
    http_conn.putrequest('GET', url, skip_accept_encoding=True)
    http_conn.putheader("Accept", "text/html")
    http_conn.putheader("Accept", "text/plain")
    http_conn.putheader("User-Agent", get_user_agent())
    http_conn.endheaders()


def get_url(url, http_conn, verbose):
    if verbose >= 1:
        print "getting url", url
    lagged = False
    try:
        send_request(http_conn, url)
        http_result = http_conn.getresponse()
        if verbose >= 1:
            print "status is", http_result.status
        if http_result.status != 200:
            handle_http_errors(http_conn, http_result, verbose)
    except:
        sys.stderr.write("failed to retrieve output from %s\n" % url)
        return None, None

    contents = http_result.read()
    if verbose >= 2:
        print "contents is", contents
    http_conn.close()

    # format <error code="maxlag"
    error_pattern = re.compile("<error code=\"([^\"]+)\"")
    result = error_pattern.search(contents)
    if result:
        if result.group(1) == "maxlag":
            lagged = True
        else:
            sys.stderr.write("Error '%s' encountered\n" % result.group(1))
            return None
    else:
        lagged = False
    return lagged, contents


def get_pages_param(pageids):
    return '&pageids=' + '|'.join(pageids)


def get_user_ids_from_content(content):
    try:
        return [userids['userid'] for pageid in content['query']['pages'].keys()
                for userids in content['query']['pages'][pageid]['revisions']]
    except:
        raise
        return []


def get_pages_todo(pageids, batch_start, batch_size):
    if batch_start > len(pageids):
        return None
    return pageids[batch_start:batch_start + batch_size]


def get_cat_userids(pageids, wikiname, verbose):
    api_params = ('action=query&prop=revisions&rvprop=userid'
                  '&format=json')
    api_url_templ = 'https://{wiki}/w/api.php?' + api_params
    api_url = api_url_templ.format(wiki=wikiname)
    user_ids = []
    http_conn = httplib.HTTPSConnection(wikiname)
    batch_start = 0
    batch_size = 50
    while True:
        if verbose >= 2:
            print "doing batch of pages from", batch_start
        pages_to_do = get_pages_todo(pageids, batch_start, batch_size)
        if pages_to_do is None:
            return user_ids
        api_url_chunk = api_url + get_pages_param(pages_to_do)
        if verbose >= 2:
            print "url is", api_url_chunk
        lagged, contents = get_url(api_url_chunk, http_conn, verbose)
        if lagged:
            sys.stderr.write("lagged, sleeping 5 seconds")
            time.sleep(5)
            continue
        contents = json.loads(contents)
        if verbose >= 2:
            print "extending by", get_user_ids_from_content(contents)
        user_ids.extend(get_user_ids_from_content(contents))
        batch_start = batch_start + batch_size


def get_continue_info(contents):
    try:
        return contents['continue']['gcmcontinue']
    except:
        return None


def get_pageids_from_content(content):
    try:
        return content['query']['pages'].keys()
    except:
        return []


def get_pageids_in_cat(catname, wikiname, verbose):
    api_params = ('action=query&generator=categorymembers&gcmtitle={category}'
                  '&gcmprop=ids&gcmtype=file&format=json&gcmlimit=50')
    api_url_templ = 'https://{wiki}/w/api.php?' + api_params
    api_url = api_url_templ.format(wiki=wikiname, category=catname)
    api_url_chunk = api_url
    done = False
    pageids = []
    http_conn = httplib.HTTPSConnection(wikiname)
    while not done:
        if verbose >= 2:
            print "url is", api_url_chunk
        lagged, contents = get_url(api_url_chunk, http_conn, verbose)
        if lagged:
            sys.stderr.write("lagged, sleeping 5 seconds")
            time.sleep(5)
            continue
        contents = json.loads(contents)
        if verbose >= 2:
            print "extending by", get_pageids_from_content(contents)
        pageids.extend(get_pageids_from_content(contents))
        continue_param = get_continue_info(contents)
        if verbose >= 2:
            print "continue param", continue_param
        if continue_param is None:
            done = True
        else:
            api_url_chunk = api_url + '&gcmcontinue=' + continue_param
    return pageids


def get_cat_name(category):
    return 'Category:' + category.replace(' ', '_')


def do_main(verbose=0):
    category = 'Images from Wiki Loves Monuments 2016 in Greece'
    wikiname = 'commons.wikimedia.org'
    pageids = get_pageids_in_cat(get_cat_name(category), wikiname, verbose)
    if verbose >= 1:
        print "page ids are...", pageids
    print "total pages in category:", len(pageids)
    user_ids = get_cat_userids(pageids, wikiname, verbose)
    user_ids = list(set(user_ids))
    if verbose >= 1:
        print "user ids are...", user_ids
    print "total contributors to category:", len(user_ids)


if __name__ == '__main__':
    do_main(verbose=1)
