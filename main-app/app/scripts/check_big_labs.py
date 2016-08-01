from setup import DB, get_labs_web, get_student_name, get_task_number
from diff_report import generateLabReport
from global_info import CHECK_LABS, STUDENT_ID_FOLDER
from check_labs import get_lab_status, set_lab_status, set_diff_percent

import datetime
import sqlite3
import os
import subprocess
from natsort import natsorted
from shutil import copyfile
import pwd
import grp
import os


DB = 'grade_system.sqlite'
PATH = '/home/nata/grade_system/main_app/gdisk_ccie/'
path_answer_big_lab = PATH + '_labs_answer_expert_only/big_labs/'
path_student = PATH + '_students_answer/'
report_path = '/home/nata/grade_system/main_app/reports/'


today_data = datetime.date.today().__str__()
labs_to_check = CHECK_LABS[today_data]
lab_status_values = ['Failed', 'Done', 'NotLoaded', 'ReportGenerated', 'NotComplete', 'ReportSended']


def chown(path, user, group, recursive=False):
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    if recursive:
        for root, dirs, files in os.walk(path):
            for momo in dirs:
                os.chown(os.path.join(root, momo), uid, gid)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)
    else:
        os.chown(path, uid, gid)


def check_student_BIG_lab_files(db_name, st_id, lab_id):
    lab_name = 'lab%03d' % (int(lab_id)-1000)
    st_gdisk_big_lab_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
    all_stu_files_loaded = True

    path_a = path_answer_big_lab + lab_name+'/'
    path_s = path_student + st_gdisk_big_lab_folder +lab_name+'/'
    if not os.path.exists(path_s):
        return False

    lab_files = [f for f in os.listdir(path_a) if f.endswith('.txt') and (f.startswith('r') or f.startswith('sw'))]
    stu_files = [f for f in os.listdir(path_s) if f.endswith('.txt') and (f.startswith('r') or f.startswith('sw'))]

    #print lab_files
    #print stu_files

    if len(stu_files) == 0 or not (len(lab_files) == len(stu_files)):
        return False

    return all_stu_files_loaded


def check_new_loaded_BIG_labs(verbose=True):
    st_id_range = range(1, 15)
    output = []
    for st_id in st_id_range:
        #for lab_id in labs_to_check:
        for lab_id in [1001, 1002]:
            #print st_id, lab_id
            lab_status_values = ['Failed', 'Done', 'ReportGenerated', 'Sended(Done)']
            lab_status = get_lab_status(DB,st_id,lab_id)
            if lab_status in lab_status_values:
                pass
            elif lab_status == None and check_student_BIG_lab_files(DB, st_id, lab_id):
                set_lab_status(DB, st_id, lab_id, 'Loaded')
                if verbose:
                    print "Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id)
                else:
                    output.append("Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id))
    return output


def get_info_for_BIG_lab_status(status):
    query = "select st_id, lab_id from results where status = ? and lab_id > 1000"

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


def generate_report_for_loaded_BIG_labs(verbose=True):
    loaded_labs = get_info_for_BIG_lab_status('Loaded')
    output = []
    for d in loaded_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        lab_name = 'lab%03d' % (int(lab_id)-1000)
        st_gdisk_big_lab_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
        st_report_big_lab_path = report_path + STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'+lab_name+'/'

        if not os.path.exists(st_report_big_lab_path):
            subprocess.call('mkdir -p '+st_report_big_lab_path, shell=True)

        path_a_big = path_answer_big_lab + lab_name+'/'
        path_s_big = path_student + st_gdisk_big_lab_folder + lab_name+'/'

        lab_files = [f for f in os.listdir(path_a_big) if f.endswith('.txt') and (f.startswith('r') or f.startswith('sw'))]
        lab_files = natsorted(lab_files, key=lambda y: y.lower())
        percent, diff_report = generateLabReport(lab_name, 'task1', lab_files, path_a_big, path_s_big)

        fname = st_report_big_lab_path+'report_for_big_%s.txt' % lab_name
        with open(fname, 'w') as f:
            f.write(diff_report)

        if verbose:
            print "Generate report for", STUDENT_ID_FOLDER[st_id], 'big', lab_name
        else:
            output.append("Generate report for", STUDENT_ID_FOLDER[st_id], lab_name)

        set_lab_status(DB, st_id, lab_id, 'ReportGenerated')
    return output



check_new_loaded_BIG_labs()
generate_report_for_loaded_BIG_labs()
