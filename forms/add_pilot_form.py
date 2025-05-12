from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SelectField, SubmitField
from wtforms.validators import DataRequired


class AddPilotForm(FlaskForm):
    name = StringField('Имя Фамилия', validators=[DataRequired()])
    photo = FileField('Выберите фотографию', validators=[DataRequired()])
    team_id = SelectField('Выберите команду', coerce=str)
    submit = SubmitField('Добавить')