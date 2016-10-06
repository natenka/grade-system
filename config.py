# -*- coding: utf-8 -*-
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'top most secret!'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    BASE_PATH = os.path.abspath(os.path.dirname(__file__))+'/'
    GD_PATH = BASE_PATH + 'gdisk_ccie/'
    REPORT_PATH = BASE_PATH + 'reports/'

    PATH_INITIAL = GD_PATH + '_initial_configs/labs/'
    PATH_ANSWER = GD_PATH + '_answer_configs/labs/'
    PATH_STUDENT = GD_PATH + '_students_answer/'

    PATH_ANSWER_BIG_LAB = GD_PATH + '_answer_configs/big_labs/'
    PATH_INITIAL_BIG_LAB = GD_PATH + '_initial_configs/big_labs/'

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = 'CCIE за год <ccie@linkmeup.ru>'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                    'sqlite:///' + os.path.join(Config.BASE_PATH, 'user_info_dev.sqlite3')

    USER_DB = Config.BASE_PATH + 'user_info_dev.sqlite3'
    DB = Config.BASE_PATH + 'grade_system_dev.sqlite'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
            'sqlite:///' + os.path.join(Config.BASE_PATH, 'data-test.sqlite')
    DB = Config.BASE_PATH + 'grade_system_test.sqlite'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                    'sqlite:///' + os.path.join(Config.BASE_PATH, 'user_info.sqlite3')
    DB = Config.BASE_PATH + 'grade_system.sqlite'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
