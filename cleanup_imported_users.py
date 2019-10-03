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
    rev_query = 'SELECT rev_id, rev_user_text from revision;'
    try:
        cursor.execute(rev_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting rev users ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def get_actors(cursor):
    '''get rows of actor text and id from actor table, sure hope
    we get a generator instead of a ginormous list'''
    actor_query = 'SELECT actor_id, actor_name from actor;'
    try:
        cursor.execute(actor_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting rev users ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def do_update_rev(dbcursor, rev_id, fieldname, fieldvalue, old_value):
    '''given the rev id, and a dict of a field and value,
    update those columns of the rev record for that rev id'''
    update_rev_query = 'UPDATE revision SET {name} = "{value}" WHERE rev_id = {rev_id};'.format(
        name=fieldname, value=fieldvalue, rev_id=rev_id)
    try:
        print("would do:", update_rev_query, "for old value", old_value)
        dbcursor.execute(update_rev_query.encode('utf-8'))
        dbcursor.connection.commit()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for updating revision ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def do_update_actor(dbcursor, actor_id, fieldname, fieldvalue, old_value):
    '''given the actor id, and a dict of a field and value,
    update those columns of the actor record for that actor id'''
    update_actor_query = 'UPDATE actor SET {name} = "{value}" WHERE actor_id = {actor_id};'.format(
        name=fieldname, value=fieldvalue, actor_id=actor_id)
    try:
        print("would do:", update_actor_query, "for old value", old_value)
        dbcursor.execute(update_actor_query.encode('utf-8'))
        dbcursor.connection.commit()
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for updating actor ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def skip_username(username):
    if not username:
        # empty names get skipped
        return True
    if username.decode('utf8').startswith("b'"):
        return False
    return bool(not username.decode('utf8').startswith('imported>'))


def fix_username(username):
    '''given a username with the 'imported>' prefix, strip that off
    and return the plain username'''
    if username.decode('utf8').startswith('imported>'):
        return username[9:].decode('utf8')
    elif username.decode('utf8').startswith("b'"):
        return username[2:-1].decode('utf8')
    else:
        return None


def do_main():
    '''entry point'''
    # print("Remove this line in do_main and add user/password below")
    # return
    user = 'root'
    password = 'notverysecure'

    dbcursor = get_cursor(user, password)
    wiki = 'wikidatawiki'
    use_db(dbcursor, wiki)

    get_rev_users(dbcursor)
    rows = dbcursor.fetchall()
    for row in rows:
        if not row:
            done = False
            break
        if skip_username(row[1]):
            continue
        do_update_rev(dbcursor, rev_id=row[0], fieldname='rev_user_text',
                      fieldvalue=fix_username(row[1]), old_value=row[1])

    get_actors(dbcursor)
    rows = dbcursor.fetchall()
    for row in rows:
        if not row:
            done = False
            break
        if skip_username(row[1]):
            continue
        do_update_actor(dbcursor, actor_id=row[0], fieldname='actor_name',
                        fieldvalue=fix_username(row[1]), old_value=row[1])


if __name__ == '__main__':
    do_main()
