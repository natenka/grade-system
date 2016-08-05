from setup import DB, get_labs_web, get_student_name, get_task_number
from diff_report import generateLabReport
from check_labs import get_lab_status, set_lab_status, set_diff_percent
from ..settings import DB, PATH_ANSWER_BIG_LAB, REPORT_PATH, LABS_TO_CHECK, PATH_STUDENT, ST_ID_RANGE, STUDENT_ID_FOLDER
from general_func import query_db, query_db_ret_list_of_dict, cfg_files_in_dir

import datetime
import sqlite3
import os
import subprocess
import os



def check_student_BIG_lab_files(db_name, st_id, lab_id):
    lab_name = 'lab%03d' % (int(lab_id)-1000)
    st_gdisk_big_lab_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
    all_stu_files_loaded = True

    path_a = PATH_ANSWER_BIG_LAB + lab_name+'/'
    path_s = PATH_STUDENT + st_gdisk_big_lab_folder +lab_name+'/'
    if not os.path.exists(path_s):
        return False

    lab_files = cfg_files_in_dir(path_a)
    stu_files = cfg_files_in_dir(path_s)

    if len(stu_files) == 0 or not (len(lab_files) == len(stu_files)):
        return False

    return all_stu_files_loaded


def check_new_loaded_BIG_labs(verbose=True):
    output = []
    for st_id in ST_ID_RANGE:
        #for lab_id in LABS_TO_CHECK:
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

    result = query_db_ret_list_of_dict(DB, query, ['lab_id','st_id'], args=(status,))
    return result


def generate_report_for_loaded_BIG_labs(verbose=True):
    loaded_labs = get_info_for_BIG_lab_status('Loaded')
    output = []
    for d in loaded_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        lab_name = 'lab%03d' % (int(lab_id)-1000)
        st_gdisk_big_lab_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
        st_report_big_lab_path = REPORT_PATH + STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'+lab_name+'/'

        if not os.path.exists(st_report_big_lab_path):
            subprocess.call('mkdir -p '+st_report_big_lab_path, shell=True)

        path_a_big = PATH_ANSWER_BIG_LAB + lab_name+'/'
        path_s_big = PATH_STUDENT + st_gdisk_big_lab_folder + lab_name+'/'


        lab_files = cfg_files_in_dir(path_a_big)
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
