#!/usr/bin/env python2
# coding: utf-8

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, Users
import random, string

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Fake itens
categories = [
    {
        "id": 1,
        "name": "Soccer",
    },
    {
        "id": 2,
        "name": "Basketball",
    },
    {
        "id": 3,
        "name": "Volleyball",
    }
]

items = [
    {
        "id": 1,
        "title": "Soccer Ball",
        "description": "It's a ball",
        "category_id": 1,
        "user_id": 1
    },
    {
        "id": 2,
        "title": "Basket",
        "description": "It's a basket",
        "category_id": 2,
        "user_id": 1
    },
    {
        "id": 3,
        "title": "Shoes",
        "description": "It's a shoes",
        "category_id": 1,
        "user_id": 1
    }
]


@app.route('/')
@app.route('/catalog')
def showCatalog():
    categories = session.query(Categories).all()
    items = session.query(Items.title, Categories.name.label('category_name')).join(Items.category).all()
    return render_template("catalog.html", categories = categories, items = items, category_name = None)

@app.route('/catalog/<category_name>')
@app.route('/catalog/<category_name>/items')
def showAllItems(category_name):
    category = [category for category in categories if category["name"].lower() == category_name.lower()]
    if not len(category):
        flash("Category not found")
        return redirect(url_for('showCatalog'))

    category_id = category[0]["id"]
    category_name = category[0]["name"]
    filtered_items = [item for item in items if item["category_id"] == category_id]
    return render_template("catalog.html", categories = categories, items = filtered_items, category_name = category_name)

@app.route('/catalog/<category_name>/<item_name>')
def showItem(category_name, item_name):
    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        return render_template("item.html", category_name = category_name, item = item)
    else:
        return return_value

@app.route('/catalog/new', defaults={'category_name': None}, methods=["GET", "POST"])
@app.route('/catalog/<category_name>/new', methods=["GET", "POST"])
def addItem(category_name):
    if request.method == 'POST':
        flash("New item created")
        if category_name:
            return redirect(url_for('showAllItems', category_name = category_name))
        else:
            return redirect(url_for('showCatalog'))

    if category_name:
        category = [category for category in categories if category["name"].lower() == category_name.lower()]
        if not len(category):
            return redirect(url_for('addItem'))
    return render_template("newitem.html", category_name = category_name, categories = categories)

@app.route('/catalog/<category_name>/<item_name>/edit', methods=["GET", "POST"])
def editItem(category_name, item_name):
    if request.method == 'POST':
        flash("Item edited")
        return redirect(url_for('showItem', category_name = category_name, item_name = item_name))

    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        return render_template("edititem.html", category_name = category_name, categories = categories, item = item)
    else:
        return return_value

@app.route('/catalog/<category_name>/<item_name>/delete', methods=["GET", "POST"])
def deleteItem(category_name, item_name):
    if request.method == 'POST':
        flash("Item deleted")
        return redirect(url_for('showAllItems', category_name = category_name))

    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        return render_template("deleteitem.html", category_name = category_name, item = item)
    else:
        return return_value

def checkCategoryAndItem(category_name, item_name):
    category = [category for category in categories if category["name"].lower() == category_name.lower()]
    if not len(category):
        flash("Category not found")
        return None, redirect(url_for('showCatalog'))

    category_id = category[0]["id"]
    category_name = category[0]["name"]

    item = [item for item in items if (item["title"].lower() == item_name.lower() and item["category_id"] == category_id)]
    if not len(item):
        flash("Item not found in '%s'" % category_name)
        return None, redirect(url_for('showAllItems', category_name = category_name.lower()))

    return item[0], None


# Endpoints para a API

@app.route('/catalog.json')
def showCatalogJSON():
    return "Exibindo todo o catálogo em JSON"

@app.route('/catalog/<category_name>.json')
def showAllItemsJSON(category_name):
    return "Exibindo Items de '%s' em JSON" % category_name

@app.route('/catalog/<category_name>/<item_name>.json')
def showItemJSON(category_name, item_name):
    return "Exibindo item '%s' de '%s' em JSON" % (item_name, category_name)


if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    app.run(host='0.0.0.0', port=8000)
