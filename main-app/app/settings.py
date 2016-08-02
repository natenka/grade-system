import os
import datetime

from scripts.lab_check_schedule import CHECK_LABS


# Path variables
PATH = '/Users/natasha/Programming/grade-system/main-app/'
GD_PATH = PATH + ''
REPORT_PATH = PATH + 'reports/'

PATH_INITIAL = GD_PATH + '_initial_configs/labs/'
PATH_ANSWER = GD_PATH + '_labs_answer_expert_only/labs/'
PATH_STUDENT = GD_PATH + '_students_answer/'

PATH_ANSWER_BIG_LAB = GD_PATH + '_labs_answer_expert_only/big_labs/'
PATH_INITIAL_BIG_LAB = GD_PATH + '_initial_configs/big_labs/'

# Development DB
DB = PATH + 'grade_system_dev.sqlite'

# Current student ID range
ST_ID_RANGE = range(1,15)


today_data = datetime.date.today().__str__()
LABS_TO_CHECK = CHECK_LABS[today_data]
if not LABS_TO_CHECK:
    LABS_TO_CHECK = CHECK_LABS[(datetime.date.today()+datetime.timedelta(days=2)).__str__()]
