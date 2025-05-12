import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase
from sqlalchemy import orm
from flask_login import UserMixin


class Pilot(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'pilot'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    photo = sqlalchemy.Column(sqlalchemy.LargeBinary)
    team_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("team.id"))
    team = orm.relationship('Team')
