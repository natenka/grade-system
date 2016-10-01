from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, IntegerField, SelectField
from wtforms.validators import Required, Length


class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 16)])
    password = PasswordField('Password', validators=[Required()])
    # Add 'remember me' function
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')


class LabForm(Form):
    comment = TextAreaField('\nAdd comment (optional)')
    mark = IntegerField('Enter lab mark', validators=[Required()])
    done = SubmitField('Done')


class EditReportForm(Form):
    report = TextAreaField('Report')
    save_report = SubmitField('Save Report')


class ShowReportForm(Form):
    select_st_id = SelectField('Select ST ID', choices = [])
    select_lab_id = SelectField('Select Lab ID', choices = [])
    open_report = SubmitField('Open report')
    regenerate_report = SubmitField('Regenerate report')


class SyncGdriveForm(Form):
    sync_config = SubmitField('Sync Configs')


class SyncStuGdriveForm(Form):
    sync_students = SubmitField('Sync Students')


class SendCheckedLabsForm(Form):
    confirm = BooleanField('Confirm')
    send = SubmitField('Send')


class SendMailToAllStudentsForm(Form):
    header = TextAreaField('Enter email header', validators=[Required()])
    message = TextAreaField('Add email message', validators=[Required()])
    all_confirm = BooleanField('Confirm')
    all_send = SubmitField('Send')

class RegisterUserForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 16)])
    password = PasswordField('Password', validators=[Required()])
    email = StringField('Email', validators=[Required(), Length(1, 32)])
    register = SubmitField('Register')
