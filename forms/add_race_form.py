from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired


class AddRaceForm(FlaskForm):
    title = StringField('Название этапа', validators=[DataRequired()])
    race_date = DateField('Дата гонки', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    image1 = FileField('Фото 1', validators=[DataRequired()])
    image2 = FileField('Фото 2', validators=[DataRequired()])
    submit = SubmitField('Добавить')