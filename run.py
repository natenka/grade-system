#!/usr/bin/env python
from app import create_app, db
from app.models import User, Role
from config import config
from flask.ext.script import Manager, Shell
from flask.ext.migrate import MigrateCommand
import commands


manager = Manager(create_app)
manager.add_option("-c", "--config", dest="config_name",
                   required=False, default=config['development'])

def make_shell_context():
    return dict(app=create_app('development'), db=db, User=User, Role=Role)
#    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                #Permission=Permission, Post=Post, Comment=Comment)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
