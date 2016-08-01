from setup import DB, get_labs_web, get_student_name, get_task_number
from diff_report import generateLabReport
from global_info import CHECK_LABS, STUDENT_ID_FOLDER
import datetime
import sqlite3
import os
import subprocess
from natsort import natsorted

#Test DB
#DB = 'db.sqlite'
DB = 'grade_system.sqlite'
PATH = '/Users/natasha/Programming/grade-system/gdisk_ccie/'
path_answer = PATH + '_labs_answer_expert_only/labs/'
path_student = PATH + '_students_answer/'
report_path = '/Users/natasha/Programming/grade-system/reports/'

path_answer_big_lab = PATH + '_labs_answer_expert_only/big_labs/'


#Test
#path_answer = PATH + '_initial_configs/labs/'
#path_student = PATH + '_labs_answer_expert_only/labs/'


today_data = datetime.date.today().__str__()
labs_to_check = CHECK_LABS[today_data]
if not labs_to_check:
    labs_to_check = CHECK_LABS[(datetime.date.today()+datetime.timedelta(days=2)).__str__()]

lab_status_values = ['Failed', 'Done', 'NotLoaded', 'ReportGenerated', 'NotComplete', 'ReportSended']


def set_mark_in_db(db_name, st_id, lab_id, mark):
    """
    Set mark in DB for st_id, lab_id
    """
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "update results set mark = '%s' where st_id = %s and lab_id = %s" % (mark, st_id, lab_id)
        cursor.execute(query)


def save_comment_in_db(db_name, st_id, lab_id, comment):
    """
    Set comments for st_id, lab_id
    """
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = """update results set comments = "%s" where st_id = %s and lab_id = %s""" % (comment, st_id, lab_id)
        cursor.execute(query)


def set_expert_name(db_name, st_id, lab_id, expert):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "update results set expert = '%s' where st_id = %s and lab_id = %s" % (expert, st_id, lab_id)
        cursor.execute(query)


def get_all_emails_from_db(db_name):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "select st_email from students"
        cursor.execute(query)
        emails = cursor.fetchall()
        return emails


def get_comment_mark_and_email_from_db(db_name, st_id, lab_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "select comments, mark from results where lab_id = ? and st_id = ?"
        cursor.execute(query, (lab_id,st_id))
        result = cursor.fetchone()
        comment = ''
        if len(result) == 2:
            comment, mark = result
        else:
            mark = result[0]
        query = "select st_email from students where st_id = ?"
        cursor.execute(query, (st_id,))
        email = cursor.fetchone()
        email = email[0]
        return comment, email, mark


def get_all_comments_for_lab(db_name, lab_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "select comments from results where lab_id = ?"
        cursor.execute(query, (lab_id,))
        comments = cursor.fetchall()
        result = []
        for comment in comments:
            if comment[0]:
                result.append(comment[0])
        return set(result)


def get_lab_status(db_name, st_id, lab_id):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "select status from results where lab_id = ? and st_id = ?"
        cursor.execute(query, (lab_id,st_id))
        status = cursor.fetchone()
        if status:
            status = status[0]
        return status


def set_lab_status(db_name, st_id, lab_id, lab_status):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        if get_lab_status(db_name, st_id, lab_id):
            query = "update results set status = '%s' where st_id = %s and lab_id = %s" % (lab_status, st_id, lab_id)
            cursor.execute(query)
        else:
            query = "insert into results (st_id, lab_id, status) values (?,?,?)"
            cursor.execute(query, (st_id, lab_id, lab_status))


def set_diff_percent(db_name, st_id, lab_id, percent):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        query = "update results set diff = '%s' where st_id = %s and lab_id = %s" % (percent, st_id, lab_id)
        cursor.execute(query)


def check_student_lab_files(db_name, st_id, lab_id):
    lab_name = 'lab%03d' % int(lab_id)
    task_n = get_task_number(db_name,lab_id)
    st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
    all_stu_files_loaded = True

    for n in range(1,task_n+1):
        task = 'task' + str(n)
        path_a = path_answer +  lab_name+'/' + task+'/'
        path_s = path_student + st_gdisk_folder +lab_name+'/' + task+'/'
        if not os.path.exists(path_s):
            return False
        if not os.path.exists(path_a):
            return False
        lab_files = [f for f in os.listdir(path_a) if f.endswith('txt') and (f.startswith('r') or f.startswith('sw'))]
        stu_files = [f for f in os.listdir(path_s) if f.endswith('txt') and (f.startswith('r') or f.startswith('sw'))]
        #print lab_files
        #print stu_files

        if len(stu_files) == 0 or not (len(lab_files) == len(stu_files)):
            return False
    return all_stu_files_loaded


def check_new_loaded_labs(verbose=True):
    st_id_range = range(1, 15)
    output = []
    range_labs = range(1,max(labs_to_check)+1)

    for st_id in st_id_range:
        #for lab_id in labs_to_check:
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

    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (status,))
        result=[]
        for row in cursor.fetchmany(40):
            di = {}
            for k in ['lab_id','st_id']:
                di[k] = row[k]
            result.append(di)
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
        st_report_path = report_path + STUDENT_ID_FOLDER[st_id]+'/'+'labs/'+lab_name+'/'
        if not os.path.exists(st_report_path):
            subprocess.call('mkdir '+st_report_path,shell=True)
        diff_report = {}

        tasks_percent = []
        for n in range(1,task_n+1):
            task = 'task' + str(n)
            path_a = path_answer +  lab_name+'/' + task+'/'
            path_s = path_student + st_gdisk_folder +lab_name+'/' + task+'/'
            lab_files = [f for f in os.listdir(path_a) if f.endswith('txt') and (f.startswith('r') or f.startswith('sw'))]
            lab_files = natsorted(lab_files, key=lambda y: y.lower())
            percent, diff_report[task] = generateLabReport(lab_name, task, lab_files, path_a, path_s)
            tasks_percent.append(str(round(percent)))
        #Write separate report for lab tasks
        for task, report in diff_report.items():
            fname = st_report_path+'report_for_%s_%s.txt' % (lab_name, task)
            with open(fname, 'w') as f:
                f.write(report)
            if verbose:
                print "Generate report for", STUDENT_ID_FOLDER[st_id], lab_name, task
            else:
                output.append("Generate report for", STUDENT_ID_FOLDER[st_id], lab_name, task)
        set_lab_status(DB, st_id, lab_id, 'ReportGenerated')
        set_diff_percent(DB, st_id, lab_id, ','.join(tasks_percent))
    return output



check_new_loaded_labs()
generate_report_for_loaded_labs()
