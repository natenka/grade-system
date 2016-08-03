from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, IntegerField, SelectField
from wtforms.validators import Required, Length
from ..settings import ST_ID_RANGE, LAB_ID_RANGE, STUDENT_ID_FOLDER


class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1, 16)])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit')


class LabForm(Form):
    comment = TextAreaField('\nAdd comment (optional)')
    mark = IntegerField('Enter lab mark', validators=[Required()])
    submit_grade = BooleanField('Submit grade', validators=[Required()])
    failed = SubmitField('Failed')
    done = SubmitField('Done')


class EditReportForm(Form):
    report = TextAreaField('Report', validators=[Required()])
    save_report = SubmitField('Save Report')


class ShowReportForm(Form):
    select_st_id = SelectField('Select ST ID',
                               choices = STUDENT_ID_FOLDER.items(),
                               validators=[Required()])
    select_lab_id = SelectField('Select Lab ID',
                                choices = zip(LAB_ID_RANGE,["lab "+str(i) for i in LAB_ID_RANGE]),
                                validators=[Required()])
    open_report = SubmitField('Open report')


class SyncGdriveForm(Form):
    sync_config = SubmitField('Sync Configs')


class SyncStuGdriveForm(Form):
    sync_students = SubmitField('Sync Students')


class SendCheckedLabs(Form):
    confirm = BooleanField('Confirm')
    send = SubmitField('Send')


class SendMailToAllStudentsForm(Form):
    header = TextAreaField('Enter email header')
    message = TextAreaField('Add email message')
    confirm = BooleanField('Confirm')
    send = SubmitField('Send')
