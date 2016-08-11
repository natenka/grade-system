from diff_report import generateLabReport
from ..settings import LABS_TO_CHECK, ST_ID_RANGE, LAB_ID_RANGE
from general_func import query_db, query_db_ret_list_of_dict, cfg_files_in_dir

import datetime
import sqlite3
import os
import subprocess
from collections import OrderedDict as odict


### Get functions

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


def get_results_web(db_name, all_st=True):
    """
    """
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


def get_st_list_not_done_lab(db_name):
    """
    """
    lab_dict = odict()
    today_data = datetime.date.today().__str__()

    for lab_id in LAB_ID_RANGE:
        query = "select st_id from results where lab_id = ?"
        st_done = [st[0] for st in query_db(db_name, query, args=(lab_id,))]
        lab_dict[lab_id] = ', '.join([str(st) for st in ST_ID_RANGE if not st in st_done])

    return lab_dict


def get_comment_email_mark_from_db(db_name, st_id, lab_id):
    """
    """
    query = "select comments, st_email, mark from results, students where lab_id = ? and results.st_id = ? and results.st_id = students.st_id"
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
    return set([comment for comment in comments if comment[0]])


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

    query = '''update results set status = '%s', comments = '%s', mark = '%s', expert = '%s', check_time = '%s' where st_id = ? and lab_id = ?''' % (status, comment, mark, expert, today_data)

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
    lab_name = 'lab%03d' % int(lab_id)
    task_n = get_task_number(db_name,lab_id)
    st_gdisk_folder = config['STUDENT_ID_FOLDER'][st_id]+'/'+'labs/'
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
    range_labs = range(1,max(config['LABS_TO_CHECK'])+1)

    for st_id in ST_ID_RANGE:
        #for lab_id in LABS_TO_CHECK:
        for lab_id in range_labs:
            lab_status_values = ['Failed', 'Done', 'ReportGenerated', 'Sended(Done)']
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
    STUDENT_ID_FOLDER = config['STUDENT_ID_FOLDER']
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
    st_gdisk_big_lab_folder = config['STUDENT_ID_FOLDER'][st_id]+'/'+'big_labs/'
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
    for st_id in ST_ID_RANGE:
        #for lab_id in LABS_TO_CHECK:
        for lab_id in [1001, 1002]:
            #print st_id, lab_id
            lab_status_values = ['Failed', 'Done', 'ReportGenerated', 'Sended(Done)']
            lab_status = get_lab_status(db_name,st_id,lab_id)
            if lab_status in lab_status_values:
                pass
            elif lab_status == None and check_student_BIG_lab_files(db_name, st_id, lab_id, config):
                set_lab_status(db_name, st_id, lab_id, 'Loaded')
                if verbose:
                    print "Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id)
                else:
                    output.append("Set status to 'Loaded' for lab %d student %d" % (lab_id, st_id))
    return output


def generate_report_for_loaded_BIG_labs(db_name,config,verbose=True):
    loaded_labs = get_info_for_BIG_lab_status(db_name,'Loaded')
    STUDENT_ID_FOLDER = config['STUDENT_ID_FOLDER']
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


def generate_dict_report_content(st_id, lab_id, config):
    diff_report = odict()
    STUDENT_ID_FOLDER = config['STUDENT_ID_FOLDER']

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


def return_report_content(st_id, lab_id, task, config):
    REPORT_PATH = config['REPORT_PATH']
    STUDENT_ID_FOLDER = config['STUDENT_ID_FOLDER']

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
