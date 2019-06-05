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


def get_rev_timestamps(cursor):
    '''get rows of rev timestamp and id from revision table, sure hope
    we get a generator instead of a ginormous list'''
    rev_query = 'SELECT rev_timestamp, rev_id from revision;'
    try:
        cursor.execute(rev_query.encode('utf-8'))
    except MySQLdb.Error as ex:
        raise MySQLdb.Error("exception for getting rev timestamp ({errno}:{message})".format(
            errno=ex.args[0], message=ex.args[1])) from None


def is_valid_timestamp(timestamp):
    '''check if the string is YYYYMMDDHHMMSS format
    and return True if so, False if not, None if it's None or not numeric'''
    if timestamp is None:
        return None
    if not timestamp.isdigit():
        return None
    if len(timestamp) != 14:
        return False
    century = int(timestamp[0:2])
    if century < 19 or century > 20:
        return False
    month = int(timestamp[4:6])
    if month < 1 or month > 12:
        return False
    day = int(timestamp[6:8])
    if day < 1 or day > 31:
        return False
    hours = int(timestamp[8:10])
    if hours > 23:
        return False
    minutes = int(timestamp[10:12])
    if minutes > 59:
        return False
    seconds = int(timestamp[12:14])
    if seconds > 59:
        return False
    return True

    
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
    

def fix_bad_timestamp_values(timestamp):
    '''given a timestamp of the right length but possibly with
    bad numberical values in it, fix up any such values rather
    arbitrarily and return a new value'''
    if (is_valid_timestamp(timestamp)):
        timestamp = timestamp.decode('utf-8')
        return timestamp
    timestamp = timestamp.decode('utf-8')
    century = timestamp[0:2]
    decade = timestamp[2:4]
    month = timestamp[4:6]
    day = timestamp[6:8]
    hours = timestamp[8:10]
    minutes = timestamp[10:12]
    seconds = timestamp[12:14]
    if int(century) < 19 or int(century) > 20:
        century = '20'
    if int(month) < 1 or int(month) > 12:
        month = '01'
    if int(day) < 1 or int(day) > 31:
        day = '01'
    if int(hours) > 23:
        hours = '01'
    if int(minutes) > 59:
        minutes = '01'
    if int(seconds) > 59:
        seconds = '01'
    return "{Y}{y}{M}{D}{h}{m}{s}".format(
        Y=century, y=decade, M=month, D=day, h=hours, m=minutes, s=seconds)


def fix_timestamp(timestamp):
    '''given a badly formatted timestamp, fix it up somehow'''
    if timestamp is not None:
        # convert any stray \x00 to '0'
        timestamp = timestamp.replace(b'\x00', b'0')
    if timestamp is None or not timestamp.isdigit():
        timestamp = '20010101010101'
    elif len(timestamp) != 14:
        timestamp = timestamp.ljust(14, '0')
    return fix_bad_timestamp_values(timestamp)

        
def do_main():
    '''entry point'''
    #print("Remove this line in do_main and add user/password below")
    #return
    user = 'root'
    password = 'notverysecure'

    dbcursor = get_cursor(user, password)
    wiki = 'elwikt'
    use_db(dbcursor, wiki)
    users = {}
    today = time.strftime("%Y%m%d%H%M%S", time.gmtime())

    get_rev_timestamps(dbcursor)
    rows = dbcursor.fetchall()
    for row in rows:
        if not row:
            done = False
            break
        if is_valid_timestamp(row[0]):
            continue
        do_update_rev(dbcursor, rev_id=row[1], fieldname='rev_timestamp',
                      fieldvalue=fix_timestamp(row[0]), old_value=row[0])


if __name__ == '__main__':
    do_main()
