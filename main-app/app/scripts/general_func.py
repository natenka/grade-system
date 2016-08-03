import sqlite3

def query_db(db_name, query, args=()):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        result = cursor.fetchall()
        if len(result) == 1:
            result = result[0]
        return result

def query_db_ret_list_of_dict(db_name, query, keys, args=()):
    with sqlite3.connect(db_name) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, args)
        result = []
        for row in cursor.fetchall():
            di = {}
            for k in keys:
                di[k] = row[k]
            result.append(di)
        return result
