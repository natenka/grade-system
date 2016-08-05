# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from flask import render_template, redirect, url_for, request
from flask.ext.login import login_required, login_user, logout_user, current_user
from ..models import User
from . import main
from .forms import LoginForm, LabForm, SyncGdriveForm, SyncStuGdriveForm, SendCheckedLabs, SendMailToAllStudentsForm, EditReportForm, ShowReportForm

from ..scripts.setup import get_config_diff_report, get_student_name, get_results_web, get_lab_stats_web, get_task_number, get_st_list_not_done_lab
from ..scripts.check_labs import set_lab_status, save_comment_in_db, set_mark_in_db, get_all_comments_for_lab, set_expert_name, get_comment_mark_and_email_from_db
from ..scripts.check_configs import get_all_for_loaded_configs, return_cfg_files
from ..scripts.gdrive.sync_gdrive import sync, configs_folder_id, students_folder_id, last_sync, set_last_sync, get_last_sync_time

from ..scripts.helpers import check_labs_and_generate_reports, set_lab_check_results, get_all_loaded_labs, generate_dict_report_content



from ..settings import DB, REPORT_PATH, STUDENT_ID_FOLDER


import os
import subprocess
from operator import itemgetter
from collections import OrderedDict as odict

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/labs', methods=['GET', 'POST'])
@login_required
def labs():
    #subprocess.call(['python', 'app/scripts/check_labs.py'])
    #subprocess.call(['python', 'app/scripts/check_big_labs.py'])
    check_labs_and_generate_reports()

    labs = get_all_loaded_labs(DB)
    print current_user
    return render_template('labs.html', lab_count = len(labs), labs=labs)


@main.route('/checked_labs', methods=['GET', 'POST'])
@login_required
def checked_labs():
    form = ShowReportForm()

    if 'open_report' in request.form.keys() and 'select_st_id' in request.form.keys() and 'select_lab_id' in request.form.keys():
        st_id = (request.form['select_st_id'])
        lab_id = (request.form['select_lab_id'])

        return redirect(url_for('main.report', id = lab_id+'_'+st_id))

    return render_template('checked_labs.html', form=form)


@main.route('/report/<id>', methods=['GET', 'POST'])
@login_required
def report(id):
    lab_id, st_id = [int(i) for i in str(id).split('_')]

    form = LabForm()

    #Prefill comment and mark for checked lab
    cur_comment, _, cur_mark = get_comment_mark_and_email_from_db(DB, st_id, lab_id)
    form.comment.data = cur_comment
    form.mark.data = cur_mark

    if 'submit_grade' in request.form.keys() and 'mark' in request.form.keys():
        comment = request.form['comment'] if 'comment' in request.form.keys() else ''

        if 'done' in request.form.keys():
            set_lab_check_results(DB, st_id, lab_id, 'Done', comment, request.form['mark'], current_user)
            print 'DONE with submit grade'

        elif 'failed' in request.form.keys():
            set_lab_check_results(DB, st_id, lab_id, 'Failed', comment, request.form['mark'], current_user)
            print 'FAILED with submit grade'

        return redirect(url_for('main.labs'))

    diff_report = generate_dict_report_content(st_id, lab_id)
    student = get_student_name(DB, st_id)
    print student

    return render_template('report.html', lab=lab_id, student=student,
                           st_id=st_id, diff=diff_report, form=form,
                           comments=get_all_comments_for_lab(DB, lab_id))


@main.route('/edit_report/<id>', methods=['GET', 'POST'])
@login_required
def edit_report(id):
    task = ''
    if str(id).count('_') == 2:
        lab_id, st_id, task = [int(i) for i in str(id).split('_')]
    else:
        lab_id, st_id, _, __ = [int(i) for i in str(id).split('_')]

    form = EditReportForm()
    student = get_student_name(DB, st_id)

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

    form.report.data = report

    if request.form.get('save_report'):
        with open(report_fname, 'w') as report_f:
            report_f.write(request.form['report'])
        return redirect(url_for('main.report', id=str(lab_id)+'_'+str(st_id) ))

    return render_template('edit_report.html', lab=lab_id, task=task, student=student, st_id=st_id, report=report,
            form=form)



@main.route('/lab_info', methods=['GET', 'POST'])
@login_required
def lab_info():

    labs = get_all_for_loaded_configs()
    return render_template('lab_info.html', lab_count = len(labs), labs=labs)


@main.route('/lab_initial/<lab_id>', methods=['GET', 'POST'])
@login_required
def lab_initial(lab_id):

    files = return_cfg_files(lab_id, 'initial')
    return render_template('lab_initial.html', lab=lab_id, files=files)


@main.route('/lab_answer/<lab_id>', methods=['GET', 'POST'])
@login_required
def lab_answer(lab_id):

    files = return_cfg_files(lab_id, 'answer')
    return render_template('lab_answer.html', lab=lab_id, files=files)



@main.route('/config_report/<lab_id>', methods=['GET', 'POST'])
@login_required
def config_report(lab_id):

    diff_report = get_config_diff_report(lab_id)
    return render_template('config_report.html', lab=lab_id, diff=diff_report)


@main.route('/stats')
@login_required
def stats():
    results = get_results_web(DB)
    results_by_sum_of_mark = sorted(results, key=itemgetter('total_marks'), reverse=True)

    return render_template('stats.html', results=results_by_sum_of_mark[:10])


@main.route('/best')
@login_required
def best():
    results = get_results_web(DB)
    results_by_sum_of_mark = sorted(results, key=itemgetter('total_marks'), reverse=True)
    for i,v in enumerate(results_by_sum_of_mark, 1):
        v['place'] = i

    return render_template('best.html', results=results_by_sum_of_mark)


@main.route('/best_rating')
@login_required
def best_rating():
    results = get_results_web(DB, all_st=False)
    results_by_sum_of_mark = sorted(results, key=itemgetter('total_marks'), reverse=True)
    for i,v in enumerate(results_by_sum_of_mark, 1):
        v['place'] = i

    return render_template('best_rating.html', results=results_by_sum_of_mark)


@main.route('/lab_stats')
@login_required
def lab_stats():
    lab_stats = get_lab_stats_web(DB)

    return render_template('lab_stats.html', lab_stats=lab_stats)

@main.route('/lab_debts')
@login_required
def lab_debts():
    st_not_done_lab = get_st_list_not_done_lab(DB)

    return render_template('lab_debts.html', st_not_done_lab=st_not_done_lab)


@main.route('/stu_stats')
@login_required
def stu_stats():
    results = get_results_web(DB)

    return render_template('stu_stats.html', results=results)


@main.route('/manage', methods=['GET', 'POST'])
@login_required
def manage():
    sync_gdrive_form = SyncGdriveForm()
    sync_stu_gdrive_form = SyncStuGdriveForm()
    send_lab_form = SendCheckedLabs()
    send_mail_to_all_form = SendMailToAllStudentsForm()

    if 'sync_config' in request.form.keys():
        configs_updated, _ = last_sync()
        if not configs_updated:
            sync(configs_folder_id)
            set_last_sync(update_configs=True)
    if 'sync_students' in request.form.keys():
        _, students_updated = last_sync()
        if not students_updated:
            sync(students_folder_id)
            set_last_sync(update_students=True)

    configs_upd_time, students_upd_time = get_last_sync_time()

    return render_template('manage.html', configs_upd_time=configs_upd_time, students_upd_time=students_upd_time,
            sync_gdrive=sync_gdrive_form, sync_stu_gdrive=sync_stu_gdrive_form,
            send_lab=send_lab_form, mail_to_all=send_mail_to_all_form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.verify_password(form.password.data):
            return redirect(url_for('main.login', **request.args))
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/help')
@login_required
def help():

    return render_template('help.html', s_labs=s_labs, labs=labs)


@main.app_errorhandler(404)
def not_found(e):
    return render_template('404.html')

