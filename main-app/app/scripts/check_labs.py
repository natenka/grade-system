from setup import get_labs_web, get_student_name, get_task_number
from diff_report import generateLabReport
from ..settings import DB, PATH_ANSWER, PATH_STUDENT, REPORT_PATH, LABS_TO_CHECK, ST_ID_RANGE, STUDENT_ID_FOLDER
from general_func import query_db, query_db_ret_list_of_dict, cfg_files_in_dir

import datetime
import sqlite3
import os
import subprocess


lab_status_values = ['Failed', 'Done', 'NotLoaded', 'ReportGenerated', 'NotComplete', 'ReportSended']


def set_mark_in_db(db_name, st_id, lab_id, mark):
    """
    Set mark in DB for st_id, lab_id
    """
    query = "update results set mark = '%s' where st_id = %s and lab_id = %s" % (mark, st_id, lab_id)
    query_db(db_name, query)


def save_comment_in_db(db_name, st_id, lab_id, comment):
    """
    Set comments for st_id, lab_id
    """
    query = """update results set comments = "%s" where st_id = %s and lab_id = %s""" % (comment, st_id, lab_id)
    query_db(db_name, query)


def set_expert_name(db_name, st_id, lab_id, expert):
    query = "update results set expert = '%s' where st_id = %s and lab_id = %s" % (expert, st_id, lab_id)
    query_db(db_name, query)


def get_all_emails_from_db(db_name):
    query = "select st_email from students"
    emails = query_db(db_name, query)
    return emails


def get_comment_mark_and_email_from_db(db_name, st_id, lab_id):
    query = "select comments, st_email, mark from results, students where lab_id = 14 and results.st_id = 5 and results.st_id = students.st_id"
    result = query_db(db_name, query, args = (lab_id,st_id))
    if len(result) == 3:
        comment, email, mark = result
    else:
        email, mark = result
        comment = ''
    return comment, email, mark


def get_all_comments_for_lab(db_name, lab_id):
    query = "select comments from results where lab_id = ?"
    comments = query_db(db_name, query, args = (lab_id,))
    result = []
    for comment in comments:
        if comment[0]:
            result.append(comment[0])
    return set(result)


def get_lab_status(db_name, st_id, lab_id):
    query = "select status from results where lab_id = ? and st_id = ?"
    status = query_db(db_name, query, (lab_id,st_id))
    if status:
        status = status[0]
    return status


def set_lab_status(db_name, st_id, lab_id, lab_status):
    if get_lab_status(db_name, st_id, lab_id):
        query = "update results set status = '%s' where st_id = %s and lab_id = %s" % (lab_status, st_id, lab_id)
        query_db(db_name, query)
    else:
        query = "insert into results (st_id, lab_id, status) values (?,?,?)"
        query_db(db_name, query, args = (st_id, lab_id, lab_status))


def set_diff_percent(db_name, st_id, lab_id, percent):
    query = "update results set diff = '%s' where st_id = %s and lab_id = %s" % (percent, st_id, lab_id)
    query_db(db_name, query)


def check_student_lab_files(db_name, st_id, lab_id):
    lab_name = 'lab%03d' % int(lab_id)
    task_n = get_task_number(db_name,lab_id)
    st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
    all_stu_files_loaded = True

    for n in range(1,task_n+1):
        task = 'task' + str(n)
        path_a = PATH_ANSWER +  lab_name+'/' + task+'/'
        path_s = PATH_STUDENT + st_gdisk_folder +lab_name+'/' + task+'/'
        if not os.path.exists(path_s):
            return False
        if not os.path.exists(path_a):
            return False
        lab_files = cfg_files_in_dir(path_a)
        stu_files = cfg_files_in_dir(path_s) 

        if len(stu_files) == 0 or not (len(lab_files) == len(stu_files)):
            return False
    return all_stu_files_loaded


def check_new_loaded_labs(verbose=True):
    output = []
    range_labs = range(1,max(LABS_TO_CHECK)+1)

    for st_id in ST_ID_RANGE:
        #for lab_id in LABS_TO_CHECK:
        for lab_id in range_labs:
            lab_status_values = ['Failed', 'Done', 'ReportGenerated', 'Sended(Done)']
            lab_status = get_lab_status(DB,st_id,lab_id)
            if lab_status in lab_status_values:
                pass
            elif lab_status == None and check_student_lab_files(DB, st_id, lab_id):
                set_lab_status(DB, st_id, lab_id, 'Loaded')
                if verbose:
                    print "Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id)
                else:
                    output.append("Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id))
    return output


def get_info_for_lab_status(status, all_labs=False):
    if all_labs:
        query = "select st_id, lab_id from results where status = ?"
    else:
        query = "select st_id, lab_id from results where status = ? and lab_id < 1000"

    result = query_db_ret_list_of_dict(DB, query, ['lab_id','st_id'], args=(status,))
    return result


def generate_report_for_loaded_labs(verbose=True):
    loaded_labs = get_info_for_lab_status('Loaded')
    output = []
    for d in loaded_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        print st_id, lab_id
        lab_name = 'lab%03d' % int(lab_id)
        task_n = get_task_number(DB,lab_id)
        st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
        st_REPORT_PATH = REPORT_PATH + STUDENT_ID_FOLDER[st_id]+'/'+'labs/'+lab_name+'/'
        if not os.path.exists(st_REPORT_PATH):
            subprocess.call('mkdir '+st_REPORT_PATH,shell=True)
        diff_report = {}

        tasks_percent = []
        for n in range(1,task_n+1):
            task = 'task' + str(n)
            path_a = PATH_ANSWER +  lab_name+'/' + task+'/'
            path_s = PATH_STUDENT + st_gdisk_folder +lab_name+'/' + task+'/'
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
        set_lab_status(DB, st_id, lab_id, 'ReportGenerated')
        set_diff_percent(DB, st_id, lab_id, ','.join(tasks_percent))
    return output
