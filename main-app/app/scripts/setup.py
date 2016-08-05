# -*- coding: utf-8 -*-

from diff_report import generateLabReport
from ..settings import DB, PATH_INITIAL, PATH_ANSWER, LABS_TO_CHECK, ST_ID_RANGE, LAB_ID_RANGE, PATH_ANSWER_BIG_LAB, PATH_INITIAL_BIG_LAB
from general_func import query_db, query_db_ret_list_of_dict, cfg_files_in_dir

import sqlite3
from os.path import isfile, join
import datetime
from collections import OrderedDict as odict


def get_config_diff_report(lab_n):
    diff_report = odict()
    lab_n = int(lab_n)
    if lab_n > 1000:
        lab = 'lab%03d' % (int(lab_n)-1000)

        path_big_i = PATH_INITIAL_BIG_LAB + lab+'/'
        path_big_a = PATH_ANSWER_BIG_LAB  + lab+'/'

        all_files = cfg_files_in_dir(path_big_i)

        percent, report = generateLabReport(lab, 'task1', all_files, path_big_i, path_big_a)
        diff_report['task1'] = report

    else:
        lab = 'lab%03d' % int(lab_n)
        task_n = get_task_number(DB,lab_n)

        for n in range(1,task_n+1):
            task = 'task' + str(n)
            path_i = PATH_INITIAL + lab+'/' + task+'/'
            path_a = PATH_ANSWER + lab+'/' + task+'/'
            all_files = cfg_files_in_dir(path_i)

            percent, report = generateLabReport(lab, task, all_files, path_i, path_a)
            diff_report[task] = report
    return diff_report


def get_labs_web(db_name):
    query = """
            select lab_id, results.st_id, st_name, status, diff, live
            from results,students
            where students.st_id = results.st_id and status='ReportGenerated'
            order by lab_id;
            """
    keys = ['lab_id','st_id','st_name','status','diff','live']
    result = query_db_ret_list_of_dict(db_name, query, keys)
    return result


def get_task_number(db_name, lab_id):
    query = "select task_number from labs where lab_id = ?"
    task_n = int(query_db(db_name, query, args=(lab_id,))[0])
    return task_n


def get_student_name(db_name, st_id):
    query = "select st_name from students where st_id = ?"
    name = str(query_db(db_name, query, args=(st_id,))[0])
    return name


def set_tasks_number_for_lab(db_name, lab_id, tasks):
    query = "update labs set task_number = %s where lab_id = %s" % (tasks, lab_id)
    query_db(db_name, query)


def get_lab_info(db_name):
    query = "select * from labs order by lab_id"
    keys = ['lab_id','lab_desc','task_number','init_config','answer_config']
    result = query_db_ret_list_of_dict(db_name, query, keys)
    return result


def get_results_web(db_name, all_st=True):
    results = []
    for st_id in ST_ID_RANGE:
        st_results = {}
        st_results['st_id'] = st_id
        st_results['student'] = get_student_name(db_name, st_id)
        query = "select lab_id from results where st_id = ? and (status = 'Sended(Done)' or status = 'Done') and lab_id != 1001"
        st_results['total_labs'] = len(query_db(db_name, query, args=(st_id,)))

        query = "select mark from results where st_id = ? and (status = 'Sended(Done)' or status = 'Done') and lab_id != 1001"
        all_marks = query_db(db_name, query, args=(st_id,))
        st_results['total_marks'] = sum([int(i[0]) for i in all_marks if i[0]])

        results.append(st_results)

    return results


def get_lab_stats_web(db_name):
    current_lab_results = []
    today_data = datetime.date.today().__str__()

    for lab_id in LAB_ID_RANGE:
        lab_results = {}
        lab_results['lab_id'] = lab_id
        query = "select lab_desc from labs where lab_id = ?"
        lab_results['lab_desc'] = query_db(db_name, query, args=(lab_id,))[0]

        query = "select st_id from results where lab_id = ?"
        lab_results['st_count'] = len(query_db(db_name, query, args=(lab_id,)))

        query = "select mark from results where lab_id = ?"
        if lab_results['st_count'] == 0:
            lab_results['avg_mark'] = 0
        else:
            marks = query_db(db_name, query, args=(lab_id,))
            lab_results['avg_mark'] = round(float(sum([int(i[0]) for i in marks if i[0]])) / lab_results['st_count'], 2)
        current_lab_results.append(lab_results)

    return current_lab_results


def get_st_list_not_done_lab(db_name):
    lab_dict = odict()
    today_data = datetime.date.today().__str__()

    for lab_id in LAB_ID_RANGE:
        query = "select st_id from results where lab_id = ?"
        st_done = [st[0] for st in query_db(db_name, query, args=(lab_id,))]
        lab_dict[lab_id] = ', '.join([str(st) for st in ST_ID_RANGE if not st in st_done])

    return lab_dict

