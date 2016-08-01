import os

SECRET_KEY = 'top most secret!'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
    os.path.dirname(__file__), '../user_info.sqlite3')
