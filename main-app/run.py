#!/usr/bin/env python
from app import create_app, db
from app.models import User
from config import config
from flask.ext.script import Manager, Shell
import commands

if __name__ == '__main__':

    manager = Manager(create_app)
    manager.add_option("-c", "--config", dest="config_name",
                       required=False, default=config['development'])
    #manager.add_command("test", commands.Test())
    manager.run()


    #app = create_app('development')
    #with app.app_context():
    #    db.create_all()
    #    if User.query.filter_by(username='user').first() is None:
    #        User.register('user', 'userpass')
    #app.debug = True
    #app.run(port=9090)
