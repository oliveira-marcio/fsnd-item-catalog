#!/usr/bin/env python2
# coding: utf-8

"""
Script de setup do banco.

Serve para criar as categorias utilizadas no app, visto que não há
funcionalidade implementada no app para manutenção das categorias.

Só precisa ser executado antes da primeira executado do app. Também pode ser
usado para checar as categorias existentes.
"""

from __future__ import absolute_import, unicode_literals
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Categories, Items, Users

engine = create_engine("sqlite:///catalog.db",
                       connect_args={"check_same_thread": False})
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Categorias que serão criadas no banco de dados
categories = ["Soccer", "Basketball", "VolleyBall"]

results = session.query(Categories).all()
if not results:
    for c in categories:
        category = Categories(name=c)
        session.add(category)
    session.commit()
    print "Categories loaded."
else:
    print "Categories already exist."

results = session.query(Categories).all()
print "\nCategories:\n"
for r in results:
    print "%s - %s" % (r.id, r.name)
