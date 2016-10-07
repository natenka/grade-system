import sys
from lab_check_schedule import CHECK_LABS
from datetime import date, timedelta, datetime

if __name__ == '__main__':
    START_SHIFT_DATE = raw_input("Enter date of shift in format '2016-07-18': ")
    SHIFT_DAYS = int(raw_input("Enter number of days to shift: "))

    keys = sorted(CHECK_LABS.keys())
    NOT_SHIFTED = keys[:keys.index(START_SHIFT_DATE)]
    SHIFTED = keys[keys.index(START_SHIFT_DATE):]

    shifted_schedule = {}

    for key in SHIFTED:
        updated_data = datetime.strptime(key,"%Y-%m-%d").date() + timedelta(days = SHIFT_DAYS)
        shifted_schedule[updated_data] = CHECK_LABS[key]

    with open('test_write_schedule.py', 'w') as f:
        f.write('CHECK_LABS = {\n')
        for k in sorted(NOT_SHIFTED):
            f.write("'%s':%s,\n" % (k, CHECK_LABS[k]))
        for key in sorted(shifted_schedule.keys()):
            f.write("'%s':%s,\n" % (key, shifted_schedule[key]))
        f.write('}\n')
