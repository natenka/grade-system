from werkzeug.security import generate_password_hash, check_password_hash
from . import db, lm
from flask.ext.login import UserMixin, AnonymousUserMixin


class Permission:
    USER = 0x01
    ADMIN = 0x80


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), index=True, unique=True)
    labs_to_check = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    st_id = db.Column(db.Integer)
    labs_allowed_to_check = db.Column(db.String(128))


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            admins_username = ['nata', 'Emil']
            if self.username in admins_username:
                self.role = Role.query.filter_by(permissions=0x80).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_role(self, role_id):
        self.role_id = role_id

    @staticmethod
    def register(username, password, email):
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def list_of_labs_to_check(self):
        list_labs_to_check = [int(lab) for lab in str(self.labs_allowed_to_check).split(',') if lab.isdigit()]
        return list_labs_to_check


    def get_all_checkers_labs(self):
        checkers_labs = User.query.with_entities(User.st_id, User.labs_to_check).all()
        checkers_labs_dict = { st_id: [int(i) for i in str(labs_to_check).split(',')] for st_id, labs_to_check in checkers_labs if st_id }
        return checkers_labs_dict

    def __repr__(self):
        return '{0}'.format(self.username)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.String(64), unique=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.USER, True),
            'Administrator': (Permission.ADMIN, False)
                }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


    def __repr__(self):
        return '{0}'.format(self.name)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


lm.anonymous_user = AnonymousUser


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

