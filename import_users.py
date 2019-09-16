#!/usr/bin/python3
import time
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
    use_query = 'USE ' + wiki + ';'
    try:
        cursor.execute(use_query.encode('utf-8'))
        _result = cursor.fetchall()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for use {wiki} ({errno}:{message})".format(
            wiki=wiki, errno=ex.args[0], message=ex.args[1])) from None


def get_rev_users(cursor):
    '''get rows of rev user text and id from revision table, sure hope
    we get a generator instead of a ginormous list'''
    rev_query = 'SELECT rev_user, rev_user_text from revision;'
    try:
        cursor.execute(rev_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting rev users ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def get_user_fields(user_id, user_name, today):
    fields = {'user_id': user_id,
              'user_name': user_name,
              'user_real_name': '',
              'user_password': 'NONE',
              'user_newpassword': '',
              'user_newpass_time': None,
              'user_email': '',
              'user_touched': today,
              'user_token': '*** INVALID ***',
              'user_email_authenticated': None,
              'user_email_token': None,
              'user_email_token_expires': None,
              'user_registration': None,
              'user_editcount': None,
              'user_password_expires': None}
    return fields


def do_insert(cursor, fields):
    '''
    given all the fields and values to go into the user table for a row,
    make it happen
    '''
    param_names = ','.join(fields.keys())
    param_formatting = ', '.join(["%s"] * len(fields.keys()))
    insert_user_query = 'INSERT IGNORE into user ({names}) VALUES ({formatting});'.format(
        names=param_names, formatting=param_formatting)
    try:
        print("would do:", insert_user_query, tuple(fields.values()))
        cursor.execute(insert_user_query.encode('utf-8'), tuple(fields.values()))
        cursor.connection.commit()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for inserting user ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def do_main():
    '''entry point'''
    print("Remove this line in do_main and add user/password below")
    return
    # user = 'someuser'
    # password = 'somepassword'

    dbcursor = get_cursor(user, password)
    wiki = 'elwikivoyage'
    use_db(dbcursor, wiki)
    users = {}
    today = time.strftime("%Y%m%d%H%M%S", time.gmtime())

    get_rev_users(dbcursor)
    rows = dbcursor.fetchall()
    for row in rows:
        if not row:
            done = False
            break
        if row[0] in users:
            continue
        if row[0] == 0:
            continue
        if not row[1]:
            # blank user text, something wrong with the row
            continue
        # row 0 is user id, row 1 is user name. yuck.
        users[row[0]] = row[0]
        fields = get_user_fields(row[0], row[1], today)
        do_insert(dbcursor, fields)


if __name__ == '__main__':
    do_main()
