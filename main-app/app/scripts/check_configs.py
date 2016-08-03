from setup import get_labs_web, get_student_name, get_task_number
from diff_report import generateLabReport
from ..settings import DB, PATH_ANSWER, PATH_INITIAL_BIG_LAB, PATH_ANSWER_BIG_LAB, REPORT_PATH, LABS_TO_CHECK, PATH_INITIAL
from general_func import query_db, query_db_ret_list_of_dict

import datetime
import sqlite3
import os
import subprocess
from collections import OrderedDict as odict



def get_lab_configs_status(db_name, lab_id):
    query = "select init_config, answer_config from labs where lab_id = ?"
    initial, answer = query_db(db_name, query, args=(lab_id,))
    return initial, answer


def set_lab_configs_status(db_name, lab_id, initial='', answer=''):
    """
    Check function usage
    """
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        init_status, answer_status = get_lab_configs_status(db_name, lab_id)
        if initial:
            #if init_status == 'NotLoaded':
            query = "update labs set init_config = '%s' where lab_id = %s" % (initial, lab_id)
            cursor.execute(query)
        if answer:
            query = "update labs set answer_config = '%s' where lab_id = %s" % (answer, lab_id)
            cursor.execute(query)


def set_task_number(db_name, lab_id, task_n):
    query = "update labs set task_number = %s where lab_id = %s" % (task_n, lab_id)
    query_db(db_name, query)


def check_lab_config_files(db_name, lab_id):
    lab_name = 'lab%03d' % int(lab_id)
    task_n = get_task_number(db_name,lab_id)
    if not os.path.exists(PATH_INITIAL + lab_name+'/'):
        return False
    initial_task_n = len([f for f in os.listdir(PATH_INITIAL + lab_name+'/') if f.startswith('task')])
    if initial_task_n == 0:
        return False
    else:
        set_task_number(db_name, lab_id, initial_task_n)
        task_n = initial_task_n

    all_config_files_loaded = True

    for n in range(1,task_n+1):
        task = 'task' + str(n)
        path_i = PATH_INITIAL + lab_name+'/' + task+'/'
        path_a = PATH_ANSWER +  lab_name+'/' + task+'/'

        if not os.path.exists(path_i) or not os.path.exists(path_a):
            return False
        init_files = cfg_files_in_dir(path_i)
        answ_files = cfg_files_in_dir(path_a)

        if len(init_files) == 0:
            return False
        elif not (len(init_files) == len(answ_files)):
            return False
    return all_config_files_loaded


def check_new_loaded_configs():
    for lab_id in xrange(1, 150):
        i_status, a_status = get_lab_configs_status(DB, lab_id)

        if check_lab_config_files(DB, lab_id):
            set_lab_configs_status(DB, lab_id, initial='Loaded', answer='Loaded')
            print "Set status to 'Loaded' for lab %d init and answer configs" % lab_id


def get_labs_for_configs_status(i_status='Loaded', a_status='Loaded'):
    query = "select lab_id from labs where init_config = ? and answer_config = ?"
    result = query_db_ret_list_of_dict(DB, query, ['lab_id'], args=(i_status,a_status))
    return result



def get_all_for_loaded_configs(i_status='Loaded', a_status='Loaded'):
    query = "select * from labs where init_config = ? and answer_config = ?"
    keys = ['lab_id', 'lab_desc', 'task_number', 'init_config', 'answer_config']
    result = query_db_ret_list_of_dict(DB, query, keys, args=(i_status,a_status))
    return result


def return_cfg_files(lab_id,cfg):
    lab_name = 'lab%03d' % int(lab_id)
    if cfg == 'initial':
        cfg_path = PATH_INITIAL + lab_name+'/'
    elif cfg == 'answer':
        cfg_path = PATH_ANSWER + lab_name+'/'

    task_n = get_task_number(DB,lab_id)

    files = odict()
    for n in range(1,task_n+1):
        task = 'task' + str(n)
        task_path = cfg_path + task + '/'
        cfg_files = sorted(cfg_files_in_dir(task_path))
        files[task] = odict()

        for f in cfg_files:
            with open(task_path+f) as cfg_f:
                files[task][f.split('.')[0]] = cfg_f.read()

    return files



check_new_loaded_configs()


#############################BIG Labs lower:

def check_BIG_lab_config_files(db_name, lab_id):
    lab_name = 'lab%03d' % (int(lab_id)-1000)

    if not os.path.exists(PATH_INITIAL_BIG_LAB+ lab_name+'/'):
        return False

    all_config_files_loaded = True

    path_i = PATH_INITIAL_BIG_LAB + lab_name+'/'
    path_a = PATH_ANSWER_BIG_LAB +  lab_name+'/'

    if not os.path.exists(path_i) or not os.path.exists(path_a):
        return False

    init_files = cfg_files_in_dir(path_i)
    answ_files = cfg_files_in_dir(path_a)


    if len(init_files) == 0:
        return False
    elif not (len(init_files) == len(answ_files)):
        return False

    return all_config_files_loaded


def check_new_loaded_configs_BIG():
    for lab_id in [1001, 1002]:
        i_status, a_status = get_lab_configs_status(DB, lab_id)

        if i_status == 'Loaded' and a_status == 'Loaded':
            pass
        elif check_BIG_lab_config_files(DB, lab_id):
            set_lab_configs_status(DB, lab_id, initial='Loaded', answer='Loaded')
            print "Set status to 'Loaded' for lab %d init and answer configs" % lab_id


check_new_loaded_configs_BIG()
