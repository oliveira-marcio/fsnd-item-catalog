#!/usr/bin/env python2
# coding: utf-8

from flask import Flask

app = Flask(__name__)

@app.route('/')
@app.route('/catalog')
def showCatalog():
    return "Página inicial com todos as categorias e últimos items."

@app.route('/catalog/<category_name>')
@app.route('/catalog/<category_name>/items')
def showAllItems(category_name):
    return "Items de '%s'" % category_name

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
    app.run(host='0.0.0.0', port=8000)
