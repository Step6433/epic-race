from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired


class AddTeamForm(FlaskForm):
    title = StringField('Название команды', validators=[DataRequired()])
    sponsor = StringField('Спонсор', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    submit = SubmitField('Добавить')