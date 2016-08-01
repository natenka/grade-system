# -*- coding: utf-8 -*-

import sqlite3
from os import listdir
from os.path import isfile, join
from diff_report import generateLabReport
from global_info import CHECK_LABS
import datetime
from collections import OrderedDict as odict
#Used for natural sorting
from natsort import natsorted

DB = 'grade_system.sqlite'
PATH = '/home/nata/grade_system/main_app/gdisk_ccie/'
path_answer = PATH + '_initial_configs/labs/'
path_student = PATH + '_labs_answer_expert_only/labs/'

path_big_initial = PATH + '_initial_configs/big_labs/'
path_big_answer = PATH + '_labs_answer_expert_only/big_labs/'


def get_config_diff_report(lab_n):
    diff_report = odict()
    lab_n = int(lab_n)
    if lab_n > 1000:
        lab = 'lab%03d' % (int(lab_n)-1000)

        path_big_i = path_big_initial + lab+'/'
        path_big_a = path_big_answer  + lab+'/'

        all_files = [f for f in listdir(path_big_i) if not (f.startswith('Icon') or f.startswith('test'))]
        all_files = natsorted(all_files, key=lambda y: y.lower())

        percent, report = generateLabReport(lab, 'task1', all_files, path_big_i, path_big_a)
        diff_report['task1'] = report

    else:
        lab = 'lab%03d' % int(lab_n)
        task_n = get_task_number(DB,lab_n)

        for n in range(1,task_n+1):
            task = 'task' + str(n)
            path_a = path_answer + lab+'/' + task+'/'
            path_s = path_student + lab+'/' + task+'/'
            all_files = [f for f in listdir(path_a) if not (f.startswith('Icon') or f.startswith('test'))]
            all_files = natsorted(all_files, key=lambda y: y.lower())

            percent, report = generateLabReport(lab, task, all_files, path_a, path_s)
            diff_report[task] = report
    return diff_report


def get_labs_web(db_name):
    query = """
            select lab_id, results.st_id, st_name, status, diff, live
            from results,students
            where students.st_id = results.st_id and status='ReportGenerated'
            order by lab_id;
            """
    with sqlite3.connect(db_name) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute(query)
        result=[]
        for row in cursor.fetchmany(100):
            di = {}
            for k in ['lab_id','st_id','st_name','status','diff','live']:
                di[k] = row[k]
            result.append(di)
        return result


def get_task_number(db_name, lab_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "select task_number from labs where lab_id = ?"
        cursor.execute(query, (lab_id,))
        task_n = int(cursor.fetchone()[0])
        return task_n

def get_student_name(db_name, st_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "select st_name from students where st_id = ?"
        cursor.execute(query, (st_id,))
        name = str(cursor.fetchone()[0])
        return name

def set_tasks_number_for_lab(db_name, lab_id, tasks):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "update labs set task_number = %s where lab_id = %s" % (tasks, lab_id)
        cursor.execute(query)

def get_lab_info(db_name):
    query = "select * from labs order by lab_id"

    with sqlite3.connect(db_name) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute(query)
        result=[]
        for row in cursor.fetchmany(100):
            di = {}
            for k in ['lab_id','lab_desc','task_number','init_config','answer_config']:
                di[k] = row[k]
            result.append(di)
        return result


def get_results_web(db_name, all_st=True):
    results = []
    st_id_range = range(1, 15)
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        for st_id in st_id_range:
            st_results = {}
            st_results['st_id'] = st_id
            st_results['student'] = get_student_name(db_name, st_id)
            cursor.execute("select lab_id from results where st_id = ? and (status = 'Sended(Done)' or status = 'Done') and lab_id != 1001", (st_id,))
            st_results['total_labs'] = len(cursor.fetchall())
            cursor.execute("select mark from results where st_id = ? and (status = 'Sended(Done)' or status = 'Done') and lab_id != 1001", (st_id,))
            st_results['total_marks'] = sum([int(i[0]) for i in cursor.fetchall() if i[0]])
            results.append(st_results)

    return results


def get_lab_stats_web(db_name):
    current_lab_results = []
    today_data = datetime.date.today().__str__()
    labs_to_check = CHECK_LABS[today_data]
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        if not labs_to_check:
            labs_to_check = CHECK_LABS[(datetime.date.today()+datetime.timedelta(days=2)).__str__()]
        range_labs = range(1,max(labs_to_check)+1) + [1001, 1002]
        #Удаляем лабы, которых нет
        range_labs.remove(3)
        range_labs.remove(10)
        range_labs.remove(20)
        for lab_id in range_labs:
            lab_results = {}
            lab_results['lab_id'] = lab_id
            cursor.execute("select lab_desc from labs where lab_id = ?", (lab_id,))
            lab_results['lab_desc'] = cursor.fetchone()[0]
            cursor.execute("select st_id from results where lab_id = ?", (lab_id,))
            lab_results['st_count'] = len(cursor.fetchall())
            cursor.execute("select mark from results where lab_id = ?", (lab_id,))
            if lab_results['st_count'] == 0:
                lab_results['avg_mark'] = 0
            else:
                lab_results['avg_mark'] = round(float(sum([int(i[0]) for i in cursor.fetchall() if i[0]])) / lab_results['st_count'], 2)
            current_lab_results.append(lab_results)

    return current_lab_results


def get_st_list_not_done_lab(db_name):
    lab_dict = odict()
    today_data = datetime.date.today().__str__()
    labs_to_check = CHECK_LABS[today_data]
    if not labs_to_check:
        labs_to_check = CHECK_LABS[(datetime.date.today()+datetime.timedelta(days=2)).__str__()]

    st_id_range = range(1,15)

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        range_labs = range(1,max(labs_to_check)+1) + [1001, 1002]
        range_labs.remove(3)
        range_labs.remove(10)
        range_labs.remove(20)

        for lab_id in range_labs:
            cursor.execute("select st_id from results where lab_id = ?", (lab_id,))
            st_done = [st[0] for st in cursor.fetchall()]
            lab_dict[lab_id] = ', '.join([str(st) for st in st_id_range if not st in st_done])

    return lab_dict

