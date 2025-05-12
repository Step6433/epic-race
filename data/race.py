import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase
from flask_login import UserMixin


class Race(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'race'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String)
    race_date = sqlalchemy.Column(sqlalchemy.DateTime)
    description = sqlalchemy.Column(sqlalchemy.String)
    image1 = sqlalchemy.Column(sqlalchemy.LargeBinary)
    image2 = sqlalchemy.Column(sqlalchemy.LargeBinary)
