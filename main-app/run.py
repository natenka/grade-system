#!/usr/bin/env python
from app import create_app, db
from app.models import User


if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='user').first() is None:
            User.register('user', 'userpass')
    app.debug = True
    app.run(port=8080)
