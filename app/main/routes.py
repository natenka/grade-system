# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import os
import datetime
from operator import itemgetter

from flask import render_template, redirect, url_for, request, flash
from flask.ext.login import login_required, login_user, logout_user, current_user
from flask import current_app
import traceback

from . import main
from ..models import User, Permission
from .forms import LoginForm, LabForm, SyncGdriveForm, SyncStuGdriveForm, SendCheckedLabsForm,\
                   SendMailToAllStudentsForm, EditReportForm, ShowReportForm, RegisterUserForm
from .main_helpers import check_labs_and_generate_reports, set_lab_check_results, get_all_loaded_labs,\
                          generate_dict_report_content, return_report_content,\
                          get_comment_email_mark_from_db, get_all_comments_for_lab,\
                          get_all_for_loaded_configs, return_cfg_files, get_student_name,\
                          get_results_web, get_lab_stats_web, get_st_list_not_done_lab,\
                          get_all_labs_checked_by_expert, get_config_diff_report, send_mail_with_reports,\
                          sync, configs_folder_id, students_folder_id, last_sync, set_last_sync,\
                          get_last_sync_time, st_id_gdisk, LAB_ID_RANGE, get_st_cfg_files,\
                          get_experts_stat, check_new_loaded_configs, send_mail, get_checkers_labs, send_mail_to_all_students
from ..decorators import admin_required
from .helpers.lab_check_schedule import CHECK_LABS

today_data = datetime.date.today().__str__()

if not CHECK_LABS[today_data]:
    today_data = (datetime.date.today() - datetime.timedelta(days=2)).__str__()
    MAX_LAB_ID_PUBL_ANS = min(CHECK_LABS[today_data]) - 1
else:
    MAX_LAB_ID_PUBL_ANS = min(CHECK_LABS[today_data]) - 1


@main.route('/')
def index():

    place, exp_stats = get_experts_stat(current_app.config['DB'], str(current_user))
    lab_count = len(get_all_labs_checked_by_expert(current_app.config['DB'], str(current_user)))

    return render_template('index.html', lab_count=lab_count, place=place, exp_stats=exp_stats)


@main.route('/labs', methods=['GET', 'POST'])
@login_required
def labs():
    check_labs_and_generate_reports(current_app.config['DB'], current_app.config)

    checkers_labs = User.query.with_entities(User.st_id, User.labs_to_check).all()
    all_checkers_labs = get_checkers_labs(current_app.config['DB'], checkers_labs)

    labs = get_all_loaded_labs(current_app.config['DB'])
    print current_user

    if not current_user.can(Permission.ADMIN):
        labs = filter(lambda d: d['lab_id'] in current_user.list_of_labs_to_check(), labs)

    return render_template('labs.html', lab_count = len(labs), labs=labs, all_checkers_labs=all_checkers_labs)


@main.route('/checked_labs', methods=['GET', 'POST'])
@login_required
def checked_labs():
    form = ShowReportForm()
    # Generate dynamic fields in form
    STUDENT_ID_FOLDER = st_id_gdisk(current_app.config['DB'])
    form.select_st_id.choices = [(str(i),j) for i,j in STUDENT_ID_FOLDER.items()]
    form.select_lab_id.choices = zip([str(i) for i in LAB_ID_RANGE],["lab "+str(i) for i in LAB_ID_RANGE])

    if form.validate_on_submit():
        st_id = (request.form['select_st_id'])
        lab_id = (request.form['select_lab_id'])

        return redirect(url_for('main.report', id = lab_id+'_'+st_id))
    checked_lab_cur_expert = get_all_labs_checked_by_expert(current_app.config['DB'], str(current_user))

    return render_template('checked_labs.html', checked_labs=checked_lab_cur_expert, form=form)


@main.route('/report/<id>', methods=['GET', 'POST'])
@login_required
def report(id):
    lab_id, st_id = [int(i) for i in str(id).split('_')]
    if not current_user.can(Permission.ADMIN):
        if not lab_id in current_user.list_of_labs_to_check():
            return render_template('403.html')

    today_data = str(datetime.datetime.utcnow().__str__().split('.')[0])

    form = LabForm()
    DB = current_app.config['DB']
    #Prefill comment and mark for checked lab
    cur_comment, st_email, cur_mark = get_comment_email_mark_from_db(DB, st_id, lab_id)
    form.comment.data = cur_comment
    form.mark.data = cur_mark

    student = get_student_name(DB, st_id)

    if form.validate_on_submit():
        comment = request.form['comment'] if 'comment' in request.form.keys() else ''

        set_lab_check_results(DB, st_id, lab_id, 'Done', comment, request.form['mark'], current_user, today_data)
        print "LAB %d for Student %d %s DONE with mark %s" % (lab_id, st_id, student, str(request.form['mark']))

        if current_user.can(Permission.ADMIN):
            all_checkers_labs_dict = current_user.get_all_checkers_labs()
            if st_id in all_checkers_labs_dict:
                if lab_id in all_checkers_labs_dict[st_id]:
                    user = User.query.filter_by(st_id=st_id).first()
                    current_all_labs = user.list_of_labs_to_check()
                    current_all_labs.append(lab_id)
                    current_all_labs = [ str(i) for i in sorted(list(set(current_all_labs)))]
                    user.labs_allowed_to_check = ','.join(current_all_labs)
                    send_mail(current_app, st_email,"[Lab] Now you can check lab %d" % lab_id, template='checkers')
                    send_mail_with_reports(current_app.config['DB'], current_app)

        return redirect(url_for('main.labs'))

    diff_report = generate_dict_report_content(DB, st_id, lab_id, current_app.config)
    print student

    st_config_files = get_st_cfg_files(DB, st_id, lab_id, current_app.config)

    return render_template('report.html', lab=lab_id, student=student, files=st_config_files,
                           cfg_name="student", st_id=st_id, diff=diff_report, form=form,
                           comments=get_all_comments_for_lab(DB, lab_id))


@main.route('/edit_report/<id>', methods=['GET', 'POST'])
@login_required
def edit_report(id):
    task = ''
    if str(id).count('_') == 2:
        lab_id, st_id, task = str(id).split('_')
        lab_id = int(lab_id)
        st_id = int(st_id)
    else:
        lab_id, st_id, _, __ = [int(i) for i in str(id).split('_')]

    if not current_user.can(Permission.ADMIN):
        if not lab_id in current_user.list_of_labs_to_check():
            return render_template('403.html')

    form = EditReportForm()
    student = get_student_name(current_app.config['DB'], st_id)

    report_fname, report = return_report_content(current_app.config['DB'], st_id, lab_id, task, current_app.config)
    form.report.data = report

    if form.validate_on_submit():
        with open(report_fname, 'w') as report_f:
            report_f.write(request.form['report'])
        return redirect(url_for('main.report', id=str(lab_id)+'_'+str(st_id) ))

    return render_template('edit_report.html', lab=lab_id, task=task, student=student, st_id=st_id, report=report,
            form=form)



@main.route('/lab_info', methods=['GET', 'POST'])
@login_required
def lab_info():

    check_new_loaded_configs(current_app.config['DB'], current_app.config)
    labs = get_all_for_loaded_configs(current_app.config['DB'])
    return render_template('lab_info.html', lab_count = len(labs), labs=labs)


@main.route('/lab_initial/<lab_id>', methods=['GET', 'POST'])
@login_required
def lab_initial(lab_id):
    files = return_cfg_files(current_app.config['DB'],lab_id, 'initial', current_app.config)

    if not current_user.can(Permission.ADMIN):
        if int(lab_id) > MAX_LAB_ID_PUBL_ANS and not int(lab_id) in current_user.list_of_labs_to_check():
            return render_template('403.html')

    return render_template('lab_initial.html', lab=lab_id, files=files, cfg_name="initial")


@main.route('/lab_answer/<lab_id>', methods=['GET', 'POST'])
@login_required
def lab_answer(lab_id):
    files = return_cfg_files(current_app.config['DB'], lab_id, 'answer', current_app.config)

    if not current_user.can(Permission.ADMIN):
        if int(lab_id) > MAX_LAB_ID_PUBL_ANS and not int(lab_id) in current_user.list_of_labs_to_check():
            return render_template('403.html')

    return render_template('lab_answer.html', lab=lab_id, files=files, cfg_name="answer")



@main.route('/config_report/<lab_id>', methods=['GET', 'POST'])
@login_required
def config_report(lab_id):
    diff_report = get_config_diff_report(current_app.config['DB'], lab_id, current_app.config)

    if not current_user.can(Permission.ADMIN):
        if int(lab_id) > MAX_LAB_ID_PUBL_ANS and not int(lab_id) in current_user.list_of_labs_to_check():
            return render_template('403.html')

    return render_template('config_report.html', lab=lab_id, diff=diff_report)


@main.route('/stats')
@login_required
@admin_required
def stats():
    results = get_results_web(current_app.config['DB'], current_app.config)
    results_by_sum_of_mark = sorted(results, key=itemgetter('total_marks'), reverse=True)

    return render_template('stats.html', results=results_by_sum_of_mark[:10])


@main.route('/best')
@login_required
@admin_required
def best():
    results = get_results_web(current_app.config['DB'], current_app.config)
    results_by_sum_of_mark = sorted(results, key=itemgetter('total_marks'), reverse=True)
    for i,v in enumerate(results_by_sum_of_mark, 1):
        v['place'] = i

    return render_template('best.html', results=results_by_sum_of_mark)


@main.route('/best_rating')
@login_required
@admin_required
def best_rating():
    results = get_results_web(current_app.config['DB'], current_app.config, all_st=False)
    results_by_sum_of_mark = sorted(results, key=itemgetter('total_marks'), reverse=True)
    for i,v in enumerate(results_by_sum_of_mark, 1):
        v['place'] = i

    return render_template('best_rating.html', results=results_by_sum_of_mark)


@main.route('/lab_stats')
@login_required
@admin_required
def lab_stats():
    lab_stats = get_lab_stats_web(current_app.config['DB'])

    return render_template('lab_stats.html', lab_stats=lab_stats)

@main.route('/lab_debts')
@login_required
@admin_required
def lab_debts():
    st_not_done_lab = get_st_list_not_done_lab(current_app.config['DB'], current_app.config)

    return render_template('lab_debts.html', st_not_done_lab=st_not_done_lab)


@main.route('/stu_stats')
@login_required
@admin_required
def stu_stats():
    results = get_results_web(current_app.config['DB'], current_app.config)

    return render_template('stu_stats.html', results=results)


@main.route('/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage():
    sync_gdrive_form = SyncGdriveForm()
    sync_stu_gdrive_form = SyncStuGdriveForm()
    send_lab_form = SendCheckedLabsForm()
    send_mail_to_all_form = SendMailToAllStudentsForm()

    if 'sync_config' in request.form.keys():
        configs_updated, _ = last_sync(current_app.config['BASE_PATH'])
        if not configs_updated:
            sync(configs_folder_id, current_app.config['BASE_PATH'])
            set_last_sync(current_app.config['BASE_PATH'], update_configs=True)
            return redirect(url_for('main.manage'))
    if 'sync_students' in request.form.keys():
        _, students_updated = last_sync(current_app.config['BASE_PATH'])
        if not students_updated:
            sync(students_folder_id, current_app.config['BASE_PATH'])
            set_last_sync(current_app.config['BASE_PATH'], update_students=True)
            return redirect(url_for('main.manage'))

    if 'confirm' in request.form.keys() and 'send' in request.form.keys():
        send_mail_with_reports(current_app.config['DB'], current_app)
        return redirect(url_for('main.manage'))

    if 'all_confirm' in request.form.keys() and 'all_send' in request.form.keys():
        header = send_mail_to_all_form.header.data
        message = send_mail_to_all_form.message.data
        send_mail_to_all_students(current_app.config['DB'], current_app, header, message)
        return redirect(url_for('main.manage'))

    configs_upd_time, students_upd_time = get_last_sync_time(current_app.config['BASE_PATH'])

    return render_template('manage.html', configs_upd_time=configs_upd_time, students_upd_time=students_upd_time,
            sync_gdrive=sync_gdrive_form, sync_stu_gdrive=sync_stu_gdrive_form,
            send_lab=send_lab_form, mail_to_all=send_mail_to_all_form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('main.login', **request.args))
        login_user(user, form.remember_me.data)

        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')

    return redirect(url_for('main.index'))


"""
@main.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    form = RegisterUserForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user is None:
            flash('This username already exists!')
            return redirect(url_for('main.register', **request.args))

        User.register(form.username.data, form.password.data, form.email.data)

        return redirect(url_for('main.index'))
    return render_template('register.html', form=form)
"""

@main.route('/help')
@login_required
def help():
    if not current_user.can(Permission.ADMIN):
        return render_template('help_checkers.html')

    return render_template('help.html')


@main.app_errorhandler(404)
def not_found(e):
    return render_template('404.html')


@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html')


@main.app_errorhandler(500)
def internal_server_error(e):
    today_data = str(datetime.datetime.utcnow().__str__().split('.')[0])
    error_info = """
    URL: %s
    Request Method: %s
    User: %s
    Traceback: \n%s
    """ % (request.path, request.method, current_user, traceback.format_exc())

    send_mail(current_app, "nataliya.samoylenko@gmail.com","Error occured in grade-system",'error', time=today_data, error_text=e, error_info=error_info)
    return render_template('500.html')
