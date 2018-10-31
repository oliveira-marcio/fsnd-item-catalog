from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    @property
    def serialize(self):
        return {
            'name': self.name
        }

class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(2000), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Categories)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(Users)

    @property
    def serialize(self):
        return {
            'name': self.name
        }

engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
