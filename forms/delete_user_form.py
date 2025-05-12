from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired


class DelUserForm(FlaskForm):
    id = IntegerField('ID пользователя', validators=[DataRequired()])
    submit = SubmitField('Удалить')