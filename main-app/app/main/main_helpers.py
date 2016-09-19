#!/usr/bin/python
# -*- coding: utf-8 -*-

from .helpers.diff_report import generateLabReport
from .helpers.lab_check_schedule import CHECK_LABS

import datetime
import sqlite3
import os
import sys
import yaml
import subprocess
from collections import OrderedDict as odict
from natsort import natsorted


import getpass
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from .helpers.gmail_creds import gmail_user, gmail_pwd


today_data = datetime.date.today().__str__()
LABS_TO_CHECK = CHECK_LABS[today_data]
if not LABS_TO_CHECK:
    LABS_TO_CHECK = CHECK_LABS[(datetime.date.today()+datetime.timedelta(days=2)).__str__()]


LAB_ID_RANGE = range(1,max(LABS_TO_CHECK)+1) + [1001, 1002]
absent_labs = [3,10,20]
for lab in absent_labs:
    LAB_ID_RANGE.remove(lab)


lab_status_values = ['Failed', 'Done', 'ReportGenerated', 'Sended(Done)', 'Loaded']

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


### Get functions


def get_experts_stat(db_name, current_expert):
    query = "select expert from results"
    res = set([i[0] for i in query_db(db_name, query) if i[0]])
    result = {}
    for expert in res:
        result[len(get_all_labs_checked_by_expert(db_name, expert))] = expert
    ordered_result = odict()
    for key in sorted(result, reverse=True):
        ordered_result[key] = result[key]
    place = ''
    for num, key in enumerate(ordered_result.keys(), 1):
        if len(get_all_labs_checked_by_expert(db_name, current_expert)) == int(key):
            place = num
    return place, ordered_result


def get_st_cfg_files(db_name, st_id, lab_id, config):

    STUDENT_ID_FOLDER = st_id_gdisk(db_name)

    if lab_id < 1000:
        lab_name = 'lab%03d' % int(lab_id)
        ST_GDISK_FOLDER = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
        CFG_PATH = config['PATH_STUDENT'] + ST_GDISK_FOLDER + lab_name + '/'

        task_n = get_task_number(db_name,lab_id)

        files = odict()
        for n in range(1,task_n+1):
            task = 'task' + str(n)
            task_path = CFG_PATH + task + '/'
            cfg_files = sorted(cfg_files_in_dir(task_path))
            cfg_files = natsorted(cfg_files, key=lambda y: y.lower())
            files[task] = odict()

            for f in cfg_files:
                with open(task_path+f) as cfg_f:
                    files[task][f.split('.')[0]] = cfg_f.read()

    else:
        lab_name = 'lab%03d' % (int(lab_id)-1000)
        ST_GDISK_FOLDER = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
        CFG_PATH = PATH_STUDENT + ST_GDISK_FOLDER + lab_name + '/'

        files = odict()

        cfg_files = sorted(cfg_files_in_dir(CFG_PATH))
        cfg_files = natsorted(cfg_files, key=lambda y: y.lower())
        files['task1'] = odict()

        for f in cfg_files:
            with open(CFG_PATH+f) as cfg_f:
                files['task1'][f.split('.')[0]] = cfg_f.read()
    return files


def get_all_labs_checked_by_expert(db_name, expert):
    query = """
            select lab_id, results.st_id, st_name, mark, check_time
            from results,students
            where students.st_id = results.st_id and expert=?;
            """
    keys = ['lab_id','st_id','st_name','mark', 'check_time']
    result = query_db_ret_list_of_dict(db_name, query, keys, (expert,))
    result = sorted(result, key=lambda k: k['check_time'], reverse=True)
    for d in result:
        d['check_time'] = datetime.datetime.strptime(d['check_time'], '%Y-%m-%d %H:%M:%S')

    return result

def get_config_diff_report(db_name, lab_n, config):
    """
    """
    diff_report = odict()
    lab_n = int(lab_n)
    if lab_n > 1000:
        lab = 'lab%03d' % (int(lab_n)-1000)

        path_big_i = config['PATH_INITIAL_BIG_LAB'] + lab+'/'
        path_big_a = config['PATH_ANSWER_BIG_LAB']  + lab+'/'

        all_files = cfg_files_in_dir(path_big_i)

        percent, report = generateLabReport(lab, 'task1', all_files, path_big_i, path_big_a)
        diff_report['task1'] = report

    else:
        lab = 'lab%03d' % int(lab_n)
        task_n = get_task_number(db_name,lab_n)

        for n in range(1,task_n+1):
            task = 'task' + str(n)
            path_i = config['PATH_INITIAL'] + lab+'/' + task+'/'
            path_a = config['PATH_ANSWER'] + lab+'/' + task+'/'
            all_files = cfg_files_in_dir(path_i)

            percent, report = generateLabReport(lab, task, all_files, path_i, path_a)
            diff_report[task] = report
    return diff_report


def get_all_loaded_labs(db_name):
    """
    """
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
    """
    """

    query = "select st_name from students where st_id = ?"
    name = str(query_db(db_name, query, args=(st_id,))[0])
    return name


def get_results_web(db_name, config, all_st=True):
    """
    """
    results = []
    for st_id in config['ST_ID_RANGE']:
        st_results = {}
        st_results['st_id'] = st_id
        st_results['student'] = get_student_name(db_name, st_id)
        query = """select lab_id from results
                   where st_id = ? and (status = 'Sended(Done)' or status = 'Done') and lab_id != 1001;"""
        st_results['total_labs'] = len(query_db(db_name, query, args=(st_id,)))

        query = """select mark from results
                   where st_id = ? and (status = 'Sended(Done)' or status = 'Done') and lab_id != 1001;"""
        all_marks = query_db(db_name, query, args=(st_id,))
        st_results['total_marks'] = sum([int(i[0]) for i in all_marks if i[0]])

        results.append(st_results)

    return results


def get_lab_stats_web(db_name):
    """
    """
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


def get_st_list_not_done_lab(db_name, config):
    """
    """
    lab_dict = odict()
    today_data = datetime.date.today().__str__()

    for lab_id in LAB_ID_RANGE:
        query = "select st_id from results where lab_id = ?"
        result = query_db(db_name, query, args=(lab_id,))
        if len(result) == 1:
            st_done = [result[0]]
        else:
            st_done = [st[0] for st in result]
        lab_dict[lab_id] = ', '.join([str(st) for st in config['ST_ID_RANGE'] if not st in st_done])

    return lab_dict


def get_comment_email_mark_from_db(db_name, st_id, lab_id):
    """
    """
    query = """select comments, st_email, mark from results, students
             where lab_id = ? and results.st_id = ? and results.st_id = students.st_id;"""
    result = query_db(db_name, query, (lab_id, st_id))
    if len(result) == 3:
        comment, email, mark = result
    else:
        email, mark = result
        comment = ''
    return comment, email, mark


def get_all_comments_for_lab(db_name, lab_id):
    """
    """
    query = "select comments from results where lab_id = ?"
    comments = query_db(db_name, query, args = (lab_id,))
    result = []
    if len(comments) > 1:
        result = set([comment for comment in comments if comment[0]])
    return result


def get_lab_status(db_name, st_id, lab_id):
    """
    """
    query = "select status from results where lab_id = ? and st_id = ?"
    status = query_db(db_name, query, (lab_id,st_id))
    if status:
        status = status[0]
    return status


def get_info_for_lab_status(db_name, status, all_labs=False):
    """
    """
    if all_labs:
        query = "select st_id, lab_id from results where status = ?"
    else:
        query = "select st_id, lab_id from results where status = ? and lab_id < 1000"

    result = query_db_ret_list_of_dict(db_name, query, ['lab_id','st_id'], args=(status,))
    return result


def get_info_for_BIG_lab_status(db_name, status):
    query = "select st_id, lab_id from results where status = ? and lab_id > 1000"

    result = query_db_ret_list_of_dict(db_name, query, ['lab_id','st_id'], args=(status,))
    return result


def get_lab_configs_status(db_name, lab_id):
    """
    """
    query = "select init_config, answer_config from labs where lab_id = ?"
    initial, answer = query_db(db_name, query, args=(lab_id,))
    return initial, answer


def get_all_for_loaded_configs(db_name, i_status='Loaded', a_status='Loaded'):
    """
    """
    query = "select * from labs where init_config = ? and answer_config = ?"
    keys = ['lab_id', 'lab_desc', 'task_number', 'init_config', 'answer_config']
    result = query_db_ret_list_of_dict(db_name, query, keys, args=(i_status,a_status))
    return result



### Get functions
def set_lab_check_results(db_name, st_id, lab_id, status, comment, mark, expert, today_data):
    """
    Set lab status, comment, mark, expert name
    for specified st_id and lab_id
    """

    query = '''update results set status = '%s', comments = '%s', mark = '%s', expert = '%s', check_time = '%s'
               where st_id = ? and lab_id = ?;''' % (status, comment, mark, expert, today_data)

    query_db(db_name, query, args=(st_id, lab_id))


def set_lab_status(db_name, st_id, lab_id, lab_status):
    """
    """
    if get_lab_status(db_name, st_id, lab_id):
        query = "update results set status = '%s' where st_id = %s and lab_id = %s" % (lab_status, st_id, lab_id)
        query_db(db_name, query)
    else:
        query = "insert into results (st_id, lab_id, status) values (?,?,?)"
        query_db(db_name, query, args = (st_id, lab_id, lab_status))


def set_diff_percent(db_name, st_id, lab_id, percent):
    """
    """
    query = "update results set diff = '%s' where st_id = %s and lab_id = %s" % (percent, st_id, lab_id)
    query_db(db_name, query)


def check_student_lab_files(db_name, st_id, lab_id, config):
    """
    """
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)
    lab_name = 'lab%03d' % int(lab_id)
    task_n = get_task_number(db_name,lab_id)
    st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
    all_stu_files_loaded = True

    for n in range(1,task_n+1):
        task = 'task' + str(n)
        path_a = config['PATH_ANSWER'] +  lab_name+'/' + task+'/'
        path_s = config['PATH_STUDENT'] + st_gdisk_folder +lab_name+'/' + task+'/'
        if not os.path.exists(path_s):
            return False
        if not os.path.exists(path_a):
            return False
        lab_files = cfg_files_in_dir(path_a)
        stu_files = cfg_files_in_dir(path_s)

        if len(stu_files) == 0 or not (len(lab_files) == len(stu_files)):
            return False
    return all_stu_files_loaded


def check_new_loaded_labs(db_name,config, verbose=True):
    """
    """
    output = []
    range_labs = range(1,max(LABS_TO_CHECK)+1)

    for st_id in config['ST_ID_RANGE']:
        for lab_id in range_labs:
            lab_status = get_lab_status(db_name,st_id,lab_id)
            if lab_status in lab_status_values:
                pass
            elif not lab_status and check_student_lab_files(db_name, st_id, lab_id, config):
                set_lab_status(db_name, st_id, lab_id, 'Loaded')
                if verbose:
                    print "Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id)
                else:
                    output.append("Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id))
    return output


def generate_report_for_loaded_labs(db_name, config, verbose=True):
    """
    """
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)
    loaded_labs = get_info_for_lab_status(db_name, 'Loaded')
    output = []
    for d in loaded_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        print st_id, lab_id
        lab_name = 'lab%03d' % int(lab_id)
        task_n = get_task_number(db_name,lab_id)
        st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
        st_REPORT_PATH = config['REPORT_PATH'] + STUDENT_ID_FOLDER[st_id]+'/'+'labs/'+lab_name+'/'
        if not os.path.exists(st_REPORT_PATH):
            subprocess.call('mkdir '+st_REPORT_PATH,shell=True)
        diff_report = {}

        tasks_percent = []
        for n in range(1,task_n+1):
            task = 'task' + str(n)
            path_a = config['PATH_ANSWER'] +  lab_name+'/' + task+'/'
            path_s = config['PATH_STUDENT'] + st_gdisk_folder +lab_name+'/' + task+'/'
            lab_files = cfg_files_in_dir(path_a)
            percent, diff_report[task] = generateLabReport(lab_name, task, lab_files, path_a, path_s)
            tasks_percent.append(str(round(percent)))
        #Write separate report for lab tasks
        for task, report in diff_report.items():
            fname = st_REPORT_PATH+'report_for_%s_%s.txt' % (lab_name, task)
            with open(fname, 'w') as f:
                f.write(report)
            if verbose:
                print "Generate report for", STUDENT_ID_FOLDER[st_id], lab_name, task
            else:
                output.append("Generate report for", STUDENT_ID_FOLDER[st_id], lab_name, task)
        set_lab_status(db_name, st_id, lab_id, 'ReportGenerated')
        set_diff_percent(db_name, st_id, lab_id, ','.join(tasks_percent))
    return output


# BIG labs
def check_student_BIG_lab_files(db_name, st_id, lab_id, config):
    lab_name = 'lab%03d' % (int(lab_id)-1000)
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)
    st_gdisk_big_lab_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
    all_stu_files_loaded = True

    path_a = config['PATH_ANSWER_BIG_LAB'] + lab_name+'/'
    path_s = config['PATH_STUDENT'] + st_gdisk_big_lab_folder +lab_name+'/'
    if not os.path.exists(path_s):
        return False

    lab_files = cfg_files_in_dir(path_a)
    stu_files = cfg_files_in_dir(path_s)

    if len(stu_files) == 0 or not (len(lab_files) == len(stu_files)):
        return False

    return all_stu_files_loaded


def check_new_loaded_BIG_labs(db_name, config, verbose=True):
    output = []
    for st_id in config['ST_ID_RANGE']:
        for lab_id in [1001, 1002]:
            #print st_id, lab_id
            lab_status = get_lab_status(db_name,st_id,lab_id)
            if lab_status in lab_status_values:
                pass
            elif not lab_status and check_student_BIG_lab_files(db_name, st_id, lab_id, config):
                set_lab_status(db_name, st_id, lab_id, 'Loaded')
                if verbose:
                    print "Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id)
                else:
                    output.append("Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id))
    return output


def generate_report_for_loaded_BIG_labs(db_name,config,verbose=True):
    loaded_labs = get_info_for_BIG_lab_status(db_name,'Loaded')
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)
    output = []
    for d in loaded_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        lab_name = 'lab%03d' % (int(lab_id)-1000)
        st_gdisk_big_lab_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
        st_report_big_lab_path = config['REPORT_PATH'] + STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'+lab_name+'/'

        if not os.path.exists(st_report_big_lab_path):
            subprocess.call('mkdir -p '+st_report_big_lab_path, shell=True)

        path_a_big = config['PATH_ANSWER_BIG_LAB'] + lab_name+'/'
        path_s_big = config['PATH_STUDENT'] + st_gdisk_big_lab_folder + lab_name+'/'


        lab_files = cfg_files_in_dir(path_a_big)
        percent, diff_report = generateLabReport(lab_name, 'task1', lab_files, path_a_big, path_s_big)

        fname = st_report_big_lab_path+'report_for_big_%s.txt' % lab_name
        with open(fname, 'w') as f:
            f.write(diff_report)

        if verbose:
            print "Generate report for", STUDENT_ID_FOLDER[st_id], 'big', lab_name
        else:
            output.append("Generate report for", STUDENT_ID_FOLDER[st_id], lab_name)

        set_lab_status(db_name, st_id, lab_id, 'ReportGenerated')
    return output


def set_lab_configs_status(db_name, lab_id, initial='', answer=''):
    """
    Check function usage
    """
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        init_status, answer_status = get_lab_configs_status(db_name, lab_id)
        if initial:
            query = "update labs set init_config = '%s' where lab_id = %s" % (initial, lab_id)
            cursor.execute(query)
        if answer:
            query = "update labs set answer_config = '%s' where lab_id = %s" % (answer, lab_id)
            cursor.execute(query)


def set_task_number(db_name, lab_id, task_n):
    """
    """
    query = "update labs set task_number = %s where lab_id = %s" % (task_n, lab_id)
    query_db(db_name, query)


def check_lab_config_files(db_name, lab_id, config):
    """
    """
    lab_name = 'lab%03d' % int(lab_id)
    task_n = get_task_number(db_name,lab_id)
    if not os.path.exists(config['PATH_INITIAL'] + lab_name+'/'):
        return False
    initial_task_n = len([f for f in os.listdir(config['PATH_INITIAL'] + lab_name+'/') if f.startswith('task')])
    if initial_task_n == 0:
        return False
    else:
        set_task_number(db_name, lab_id, initial_task_n)
        task_n = initial_task_n

    all_config_files_loaded = True

    for n in range(1,task_n+1):
        task = 'task' + str(n)
        path_i = config['PATH_INITIAL'] + lab_name+'/' + task+'/'
        path_a = config['PATH_ANSWER'] +  lab_name+'/' + task+'/'

        if not os.path.exists(path_i) or not os.path.exists(path_a):
            return False
        init_files = cfg_files_in_dir(path_i)
        answ_files = cfg_files_in_dir(path_a)

        if len(init_files) == 0:
            return False
        elif not (len(init_files) == len(answ_files)):
            return False
    return all_config_files_loaded


def check_new_loaded_configs(db_name, config):
    """
    """
    for lab_id in xrange(1, 150):
        i_status, a_status = get_lab_configs_status(db_name, lab_id)

        if check_lab_config_files(db_name, lab_id, config):
            set_lab_configs_status(db_name, lab_id, initial='Loaded', answer='Loaded')
            print "Set status to 'Loaded' for lab %d init and answer configs" % lab_id


def return_cfg_files(db_name,lab_id,cfg,config):
    """
    """
    lab_name = 'lab%03d' % int(lab_id)
    if cfg == 'initial':
        cfg_path = config['PATH_INITIAL'] + lab_name+'/'
    elif cfg == 'answer':
        cfg_path = config['PATH_ANSWER'] + lab_name+'/'

    task_n = get_task_number(db_name,lab_id)

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


def check_BIG_lab_config_files(db_name, lab_id, config):
    """
    """
    lab_name = 'lab%03d' % (int(lab_id)-1000)

    if not os.path.exists(config['PATH_INITIAL_BIG_LAB']+ lab_name+'/'):
        return False

    all_config_files_loaded = True

    path_i = config['PATH_INITIAL_BIG_LAB'] + lab_name+'/'
    path_a = config['PATH_ANSWER_BIG_LAB'] +  lab_name+'/'

    if not os.path.exists(path_i) or not os.path.exists(path_a):
        return False

    init_files = cfg_files_in_dir(path_i)
    answ_files = cfg_files_in_dir(path_a)


    if len(init_files) == 0:
        return False
    elif not (len(init_files) == len(answ_files)):
        return False

    return all_config_files_loaded


def check_new_loaded_configs_BIG(db_name, config):
    """
    """
    for lab_id in [1001, 1002]:
        i_status, a_status = get_lab_configs_status(db_name, lab_id)

        if i_status == 'Loaded' and a_status == 'Loaded':
            pass
        elif check_BIG_lab_config_files(db_name, lab_id, config):
            set_lab_configs_status(db_name, lab_id, initial='Loaded', answer='Loaded')
            print "Set status to 'Loaded' for lab %d init and answer configs" % lab_id


####### New func
def check_labs_and_generate_reports(db_name, config):
    generate_report_for_loaded_labs(db_name, config)
    generate_report_for_loaded_BIG_labs(db_name, config)
    check_new_loaded_labs(db_name, config)
    check_new_loaded_BIG_labs(db_name, config)


def generate_dict_report_content(db_name, st_id, lab_id, config):
    diff_report = odict()
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)

    if lab_id < 1000:
        lab_name = 'lab%03d' % int(lab_id)
        ST_REPORT_PATH = config['REPORT_PATH'] + STUDENT_ID_FOLDER[st_id]+'/'+'labs/'+lab_name+'/'
        report_files = sorted([f for f in os.listdir(ST_REPORT_PATH) if f.startswith('report')])

        for f in report_files:
            with open(ST_REPORT_PATH+f) as report_f:
                diff_report[f.split('_')[-1].split('.')[0]] = report_f.readlines()
    else:
        lab_name = 'lab%03d' % (int(lab_id)-1000)
        ST_REPORT_PATH = config['REPORT_PATH'] + STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'+lab_name+'/'
        report_files = sorted([f for f in os.listdir(ST_REPORT_PATH) if f.startswith('report')])

        for f in report_files:
            with open(ST_REPORT_PATH+f) as report_f:
                diff_report['_'.join(f.split('.')[0].split('_')[2:])] = report_f.readlines()

    return diff_report


def return_report_content(db_name, st_id, lab_id, task, config):
    REPORT_PATH = config['REPORT_PATH']
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)

    if lab_id < 1000:
        lab_name = 'lab%03d' % int(lab_id)
        ST_REPORT_PATH = REPORT_PATH + STUDENT_ID_FOLDER[st_id]+'/'+'labs/'+lab_name+'/'
        report_fname = ST_REPORT_PATH+'report_for_%s_%s.txt' % (lab_name, task)
    else:
        lab_name = 'lab%03d' % (int(lab_id)-1000)
        ST_REPORT_PATH= REPORT_PATH + STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'+lab_name+'/'
        report_fname = ST_REPORT_PATH+'report_for_big_%s.txt' % (lab_name)

    with open(report_fname) as report_f:
        report = report_f.read()

    return report_fname, report


#Send mail func
# Adapted from http://kutuma.blogspot.com/2007/08/sending-emails-via-gmail-with-python.html

gmail_user = gmail_user
gmail_pwd = gmail_pwd

def login(user):
    global gmail_user, gmail_pwd
    gmail_user = user
    gmail_pwd = getpass.getpass('Password for %s: ' % gmail_user)

def mail(to, subject, text, attach=None):
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    if attach:
        for f_attach in attach:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(f_attach, 'rb').read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f_attach))
            msg.attach(part)
    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    mailServer.sendmail(gmail_user, to, msg.as_string())
    mailServer.close()


def send_mail_to_all_students(db_name, header, message):
    all_emails = query_db(db_name, "select st_email from students")

    for e in all_emails:
        email = e[0]
        if len(email) > 3:
            mail(email, header, message)
        print email

def send_mail_with_reports(db_name, config):
    done_labs = get_info_for_lab_status(db_name, 'Done', all_labs=True)
    STUDENT_ID_FOLDER = st_id_gdisk(db_name)
    REPORT_PATH = config['REPORT_PATH']

    for d in done_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        if int(lab_id) > 1000:
            lab_name = 'lab%03d' % (int(lab_id) - 1000)
            st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
            st_REPORT_PATH = REPORT_PATH+ st_gdisk_folder +lab_name+'/'
            files_to_attach = []
            fname = st_REPORT_PATH+'report_for_big_%s.txt' % lab_name
            files_to_attach.append(fname)

            text_header = "[Lab] Big Lab %d is Done. Good Job!" % (int(lab_id) - 1000)
        else:
            lab_name = 'lab%03d' % int(lab_id)
            task_n = get_task_number(db_name,lab_id)
            st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
            st_REPORT_PATH = REPORT_PATH+ st_gdisk_folder +lab_name+'/'

            files_to_attach = []
            for n in range(1,task_n+1):
                task = 'task' + str(n)
                fname = st_REPORT_PATH+'report_for_%s_%s.txt' % (lab_name, task)
                files_to_attach.append(fname)

            text_header = "[Lab] Lab %s is Done. Good Job!" % lab_id

        print STUDENT_ID_FOLDER[st_id], lab_name
        comment, email, mark = get_comment_email_mark_from_db(db_name, st_id, lab_id)
        if not comment:
            comment = ''
        mark_text = u"\n\nБаллы за лабораторную: " + str(mark)

        text = comment + mark_text
        text = text.encode('utf-8')

        mail(email, text_header, text, files_to_attach)
        set_lab_status(db_name, st_id, lab_id, "Sended(Done)")


###### SYNC Google Drive

configs_folder_id = {
'_labs_answer_expert_only': '0B3uwAH0p4u2Nam81UEUxNUlPRGc',
'_initial_configs': '0B3uwAH0p4u2NcDR5bmpHdmZDRjA'}

students_folder_id = {'_students_answer': '0B3uwAH0p4u2NVDBta09JTVlwN00'}

def sync(folders, base_path):
    for folder, fld_id in folders.items():
        reply = subprocess.Popen(['python',
            base_path+'app/main/helpers/gdrive/drive_backup.py',
            '--drive_id', fld_id,
            '--destination', base_path+'gdisk_ccie/'])


def last_sync(base_path, configs_updated=False, students_updated=False):
    file_content = {}
    current_time = datetime.datetime.utcnow()
    configs_upd_time = datetime.datetime(2016, 4, 1, 0, 0)
    students_upd_time = datetime.datetime(2016, 4, 1, 0, 0)
    last_sync_file = base_path + 'app/main/helpers/gdrive/last_sync.yml'

    if os.path.exists(last_sync_file):
        with open(last_sync_file, 'rw') as f:
            file_content = yaml.load(f)
            if file_content:
                if 'configs_upd_time' in file_content:
                    configs_upd_time = datetime.datetime.strptime(file_content['configs_upd_time'], '%Y-%m-%d %H:%M:%S.%f')
                if 'students_upd_time' in file_content:
                    students_upd_time = datetime.datetime.strptime(file_content['students_upd_time'], '%Y-%m-%d %H:%M:%S.%f')
    if (current_time - configs_upd_time).seconds / 60 < 15:
        configs_updated=True
    if (current_time - students_upd_time).seconds / 60 < 60:
        students_updated=True

    return configs_updated, students_updated


def set_last_sync(base_path, update_configs=False, update_students=False):
    current_time = datetime.datetime.utcnow()
    last_sync_file = base_path + 'app/main/helpers/gdrive/last_sync.yml'
    with open(last_sync_file, 'r') as f:
        file_content = yaml.load(f)
        if not file_content:
            file_content = {}
        if update_configs:
            file_content['configs_upd_time'] = current_time.__str__()
        if update_students:
            file_content['students_upd_time'] = current_time.__str__()
    with open(last_sync_file, 'w') as f:
        yaml.dump(file_content, f)


def get_last_sync_time(base_path):
    last_sync_file = base_path + 'app/main/helpers/gdrive/last_sync.yml'
    with open(last_sync_file, 'r') as f:
        file_content = yaml.load(f)
        configs_upd_time = datetime.datetime.strptime(file_content['configs_upd_time'], '%Y-%m-%d %H:%M:%S.%f')
        students_upd_time = datetime.datetime.strptime(file_content['students_upd_time'], '%Y-%m-%d %H:%M:%S.%f')

    return configs_upd_time, students_upd_time
