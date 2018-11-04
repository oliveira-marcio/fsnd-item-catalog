#!/usr/bin/env python2
# coding: utf-8
from __future__ import absolute_import, unicode_literals
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Categories, Items, Users

engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
DBSession = sessionmaker(bind=engine)
session = DBSession()

categories = ["Soccer", "Basketball", "VolleyBall"]

results = session.query(Categories).all()
if not results:
    for c in categories:
        category = Categories(name = c)
        session.add(category)
    session.commit()
    print "Categories loaded."
else:
    print "Categories already exist."


# TODO: Remover tudo abaixo na versão final!!

results = session.query(Categories).all()
print "\nCategories:\n"
for r in results:
    print "%s - %s" % (r.id, r.name)

users = [
    {
        "name": "Lucas Oliveira",
        "email": "arrudadeoliveiralucas@gmail.com"
    },
    {
        "name": "Vanele Arruda",
        "email": "vanele.arruda@gmail.com"
    },
]

results = session.query(Users).all()
if not results:
    for u in users:
        user = Users(name = u["name"], email = u["email"])
        session.add(user)
    session.commit()

results = session.query(Users).all()
print "\nUsers:\n"
for r in results:
    print "%s - %s (%s)" % (r.id, r.name, r.email)

items = [
    {
        "title": "Soccer Ball",
        "description": "It's a ball",
        "category_id": 1,
        "user_id": 1
    },
    {
        "title": "Basket",
        "description": "It's a basket",
        "category_id": 2,
        "user_id": 1
    },
    {
        "title": "Shoes",
        "description": "It's a shoes",
        "category_id": 1,
        "user_id": 2
    }
]

results = session.query(Items).all()
if not results:
    for i in items:
        item = Items(title = i["title"], description = i["description"], category_id = i["category_id"], user_id = i["user_id"])
        session.add(item)
    session.commit()

results = session.query(Items).all()
print "\nItems:\n"
for r in results:
    category = session.query(Categories).filter_by(id = r.category_id).one().name
    user = session.query(Users).filter_by(id = r.user_id).one().name
    print "%s - %s / %s (%s - %s)" % (r.id, r.title, r.description, category, user)
