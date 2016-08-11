import os
import datetime

#from app.main.scripts.lab_check_schedule import CHECK_LABS
#from app.main.scripts.general_func import st_id_gdisk


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'top most secret!'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    PATH = os.path.abspath(os.path.dirname(__file__))+'/'
    GD_PATH = PATH + ''
    REPORT_PATH = PATH + 'reports/'

    PATH_INITIAL = GD_PATH + '_initial_configs/labs/'
    PATH_ANSWER = GD_PATH + '_labs_answer_expert_only/labs/'
    PATH_STUDENT = GD_PATH + '_students_answer/'

    PATH_ANSWER_BIG_LAB = GD_PATH + '_labs_answer_expert_only/big_labs/'
    PATH_INITIAL_BIG_LAB = GD_PATH + '_initial_configs/big_labs/'


    today_data = datetime.date.today().__str__()
    #LABS_TO_CHECK = CHECK_LABS[today_data]
    #if not LABS_TO_CHECK:
    #    LABS_TO_CHECK = CHECK_LABS[(datetime.date.today()+datetime.timedelta(days=2)).__str__()]

    #LAB_ID_RANGE = range(1,max(LABS_TO_CHECK)+1) + [1001, 1002]
    #absent_labs = [3,10,20]
    #for lab in absent_labs:
    #    LAB_ID_RANGE.remove(lab)

    #STUDENT_ID_FOLDER = st_id_gdisk(DB)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                    'sqlite:///' + os.path.join(Config.PATH, 'user_info.sqlite3')

    DB = Config.PATH + 'grade_system_dev.sqlite'
    ST_ID_RANGE = range(1,15)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
            'sqlite:///' + os.path.join(Config.PATH, 'data-test.sqlite')
    DB = Config.PATH + 'grade_system_test.sqlite'
    ST_ID_RANGE = range(1,15)


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                    'sqlite:///' + os.path.join(Config.PATH, 'user_info.sqlite3')
    DB = Config.PATH + 'grade_system.sqlite'
    ST_ID_RANGE = range(1,33)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
