import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'top most secret!'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    BASE_PATH = os.path.abspath(os.path.dirname(__file__))+'/'
    GD_PATH = BASE_PATH + ''
    REPORT_PATH = BASE_PATH + 'reports/'

    PATH_INITIAL = GD_PATH + '_initial_configs/labs/'
    PATH_ANSWER = GD_PATH + '_labs_answer_expert_only/labs/'
    PATH_STUDENT = GD_PATH + '_students_answer/'

    PATH_ANSWER_BIG_LAB = GD_PATH + '_labs_answer_expert_only/big_labs/'
    PATH_INITIAL_BIG_LAB = GD_PATH + '_initial_configs/big_labs/'


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
                    'sqlite:///' + os.path.join(Config.BASE_PATH, 'user_info.sqlite3')

    DB = Config.BASE_PATH + 'grade_system_dev.sqlite'
    ST_ID_RANGE = range(1,15)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
            'sqlite:///' + os.path.join(Config.BASE_PATH, 'data-test.sqlite')
    DB = Config.BASE_PATH + 'grade_system_test.sqlite'
    ST_ID_RANGE = range(1,15)


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                    'sqlite:///' + os.path.join(Config.BASE_PATH, 'user_info.sqlite3')
    DB = Config.BASE_PATH + 'grade_system.sqlite'
    ST_ID_RANGE = range(1,33)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
