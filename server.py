#!/usr/bin/env python2
# coding: utf-8

from flask import Flask, render_template, request, redirect, url_for, flash
import random, string

app = Flask(__name__)

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
    return "Exibindo item '%s' de '%s'" % (item_name, category_name)

@app.route('/catalog/new', defaults={'category_name': None}, methods=["GET", "POST"])
@app.route('/catalog/<category_name>/new', methods=["GET", "POST"])
def addItem(category_name):
    if category_name:
        return "Criando novo item em '%s'" % category_name
    else:
        return "Criando novo item"

@app.route('/catalog/<category_name>/<item_name>/edit', methods=["GET", "PUT"])
def editItem(category_name, item_name):
    return "Editando '%s' de '%s'" % (item_name, category_name)

@app.route('/catalog/<category_name>/<item_name>/delete', methods=["GET", "DELETE"])
def deleteItem(category_name, item_name):
    return "Deletando '%s' de '%s'" % (item_name, category_name)

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
