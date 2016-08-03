import sqlite3
import os
from natsort import natsorted


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


def st_id_gdisk(db_name):
    query = "select st_id, gdrive_name from students"
    result = query_db(db_name, query)
    result = {int(i):j for i,j in result}
    return result


def cfg_files_in_dir(dir_name):
    cfg_files = [
        f for f in os.listdir(dir_name) if f.endswith('txt') and (f.startswith('r') or f.startswith('sw'))]
    cfg_files = natsorted(cfg_files, key=lambda y: y.lower())
    return cfg_files
