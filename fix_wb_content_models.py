#!/usr/bin/python3
import MySQLdb


def get_cursor(user, password):
    '''
    open a connection, get and return a cursor
    '''
    host = 'localhost'
    port = 3306

    try:
        dbconn = MySQLdb.connect(host=host, port=port,
                                 user=user, passwd=password)
        print(dbconn)
        return dbconn.cursor()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error(
            "failed to connect to or get cursor from "
            "{host}:{port}, {errno}:{message}".format(
                host=host, port=port, errno=ex.args[0], message=ex.args[1])) from None


def use_db(cursor, wiki):
    '''execute a USE statement for a database'''
    use_query = 'USE ' + wiki + ';'
    try:
        cursor.execute(use_query.encode('utf-8'))
        _result = cursor.fetchall()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for use {wiki} ({errno}:{message})".format(
            wiki=wiki, errno=ex.args[0], message=ex.args[1])) from None


def get_model_id(cursor, model_name):
    '''get the content model id for the model name specified, from content model table'''
    model_query = "SELECT model_id from content_models WHERE model_name = '{model_name}';".format(
        model_name=model_name)
    try:
        cursor.execute(model_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting model id ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def get_model_page_ids(cursor, model_name):
    '''get rows from page table where content model is the model name specified, sure hope
    we get a generator instead of a ginormous list'''
    page_query = "SELECT page_id from page WHERE page_content_model = '{model_name}';".format(
        model_name=model_name)
    try:
        cursor.execute(page_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting page list ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def get_content_ids(cursor, page_id):
    '''get content ids that correspond to revisions for the given page id'''
    content_ids = []
    revs_query = "SELECT rev_id from revision WHERE rev_page = {page_id};".format(
        page_id=page_id)
    try:
        cursor.execute(revs_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting revs list for page ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None
    rev_rows = cursor.fetchall()
    for rev_row in rev_rows:
        if not rev_row:
            break
        slots_query = "SELECT slot_content_id from slots WHERE slot_revision_id = {rev_id};".format(
            rev_id=rev_row[0])
        try:
            cursor.execute(slots_query.encode('utf-8'))
        except MySQLdb.Error as ex:
            raise MySQLdb.Error("exception getting revs list for page ({errno}:{message})".format(
                errno=ex.args[0], message=ex.args[1])) from None
        slot_rows = cursor.fetchall()
        for slot_row in slot_rows:
            if not slot_row:
                break
            content_ids.append(slot_row[0])
    return content_ids


def do_update_content_row(dbcursor, content_id, content_model, model_name):
    '''given the content id, set the content model to the specified content_model'''
    update_content_row_query = 'UPDATE content SET content_model = {content_model} WHERE content_id = {content_id};'.format(
        content_id=content_id, content_model=content_model)
    try:
        print("would do:", update_content_row_query, "for content model", model_name)
        dbcursor.execute(update_content_row_query.encode('utf-8'))
        dbcursor.connection.commit()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for updating content row ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def fixup_content_model(dbcursor, model_name):
    '''find all pages with content model the specified model_name,
    find all the content rows tha correspond to that page's revisions,
    and set the content model for those content rows to the model
    corresponding to that model name'''
    model_ids = []
    get_model_id(dbcursor, model_name)
    model_rows = dbcursor.fetchall()
    for model_row in model_rows:
        if not model_row:
            break
        model_ids.append(model_row[0])
    if len(model_ids) != 1:
        raise MySQLdb.Error("expected one model with name {name} but found {count})".format(
            name=model_name, count=len(model_ids))) from None
        
    get_model_page_ids(dbcursor, model_name)
    rows = dbcursor.fetchall()
    for row in rows:
        if not row:
            break
        # get all the content ids for the revisions for this page
        content_ids = get_content_ids(dbcursor, page_id=row[0])

        for content_id in content_ids:
            do_update_content_row(dbcursor, content_id, model_ids[0], model_name)
    

def do_main():
    '''entry point'''
    print("Remove this line in do_main and add user/password below")
    return
    # user = 'someuser'
    # password = 'somepassword'

    dbcursor = get_cursor(user, password)
    wiki = 'wikidatawiki'
    use_db(dbcursor, wiki)

    fixup_content_model(dbcursor, 'wikibase-item')
    fixup_content_model(dbcursor, 'wikibase-property')


if __name__ == '__main__':
    do_main()
