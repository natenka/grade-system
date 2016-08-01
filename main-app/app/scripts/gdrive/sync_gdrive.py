import subprocess
import os
import sys
import yaml
import datetime

last_sync_file = '/home/nata/grade_system/main_app/app/scripts/gdrive/last_sync.yml'


configs_folder_id = {
'_labs_answer_expert_only': '0B3uwAH0p4u2Nam81UEUxNUlPRGc',
'_initial_configs': '0B3uwAH0p4u2NcDR5bmpHdmZDRjA'}

students_folder_id = {'_students_answer': '0B3uwAH0p4u2NVDBta09JTVlwN00'}

def sync(folders):
    for folder, fld_id in folders.items():
        reply = subprocess.Popen(['python',
            '/home/nata/grade_system/main_app/app/scripts/gdrive/drive_backup.py',
            '--drive_id', fld_id,
            '--destination', '/home/nata/grade_system/main_app/gdisk_ccie/'])
        #if reply == 0:
        #    print "Folder %s is in sync" % folder
        #else:
        #    print "Error in sync for folder " % folder


def last_sync(configs_updated=False, students_updated=False):
    file_content = {}
    current_time = datetime.datetime.now()
    configs_upd_time = datetime.datetime(2016, 4, 1, 0, 0)
    students_upd_time = datetime.datetime(2016, 4, 1, 0, 0)

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


def set_last_sync(update_configs=False, update_students=False):
    current_time = datetime.datetime.now()
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


def get_last_sync_time():
    with open(last_sync_file, 'r') as f:
        file_content = yaml.load(f)
        configs_upd_time = datetime.datetime.strptime(file_content['configs_upd_time'], '%Y-%m-%d %H:%M:%S.%f')
        students_upd_time = datetime.datetime.strptime(file_content['students_upd_time'], '%Y-%m-%d %H:%M:%S.%f')

        configs_upd_time += datetime.timedelta(hours=3)
        students_upd_time += datetime.timedelta(hours=3)

        configs_upd_time = configs_upd_time.__str__().split('.')[0]
        students_upd_time = students_upd_time.__str__().split('.')[0]
    return configs_upd_time, students_upd_time


if __name__ == '__main__':
    sync(configs_folder_id)

    if len(sys.argv) > 1:
        sync(students_folder_id)
