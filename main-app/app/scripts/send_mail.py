#!/usr/bin/python
# -*- coding: utf-8 -*-
# Adapted from http://kutuma.blogspot.com/2007/08/sending-emails-via-gmail-with-python.html

import getpass
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os

from check_labs import DB, report_path, get_info_for_lab_status, get_comment_mark_and_email_from_db, set_lab_status, get_all_emails_from_db
from setup import DB, get_labs_web, get_student_name, get_task_number
from global_info import CHECK_LABS, STUDENT_ID_FOLDER
from gmail_creds import gmail_user, gmail_pwd


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


def send_mail_to_all_students(message):
    for e in get_all_emails_from_db(DB):
        email = e[0]
        if len(email) > 3:
            mail(email, "[Lab] Big Lab 2!", message)
        print email

def send_mail_with_reports():
    done_labs = get_info_for_lab_status('Done', all_labs=True)

    for d in done_labs:
        st_id = d['st_id']
        lab_id = d['lab_id']
        if int(lab_id) > 1000:
            lab_name = 'lab%03d' % (int(lab_id) - 1000)
            st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'big_labs/'
            st_report_path = report_path + st_gdisk_folder +lab_name+'/'
            files_to_attach = []
            fname = st_report_path+'report_for_big_%s.txt' % lab_name
            files_to_attach.append(fname)

            text_header = "[Lab] Big Lab %d is Done. Good Job!" % (int(lab_id) - 1000)
        else:
            lab_name = 'lab%03d' % int(lab_id)
            task_n = get_task_number(DB,lab_id)
            st_gdisk_folder = STUDENT_ID_FOLDER[st_id]+'/'+'labs/'
            st_report_path = report_path + st_gdisk_folder +lab_name+'/'

            files_to_attach = []
            for n in range(1,task_n+1):
                task = 'task' + str(n)
                fname = st_report_path+'report_for_%s_%s.txt' % (lab_name, task)
                files_to_attach.append(fname)

            text_header = "[Lab] Lab %s is Done. Good Job!" % lab_id

        print STUDENT_ID_FOLDER[st_id], lab_name
        comment, email, mark = get_comment_mark_and_email_from_db(DB, st_id, lab_id)
        if not comment:
            comment = ''
        mark_text = u"\n\nБаллы за лабораторную: " + str(mark)

        text = comment + mark_text
        text = text.encode('utf-8')

        mail(email, text_header, text, files_to_attach)
        set_lab_status(DB, st_id, lab_id, "Sended(Done)")

send_mail_with_reports()

