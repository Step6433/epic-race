import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import orm
from data.db_session import SqlAlchemyBase
from flask_login import UserMixin


class Team(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'team'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String)
    sponsor = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    pilot = orm.relationship('Pilot', back_populates='team')
