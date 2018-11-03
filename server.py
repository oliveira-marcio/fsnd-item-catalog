#!/usr/bin/env python2
# coding: utf-8

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_setup import Base, Categories, Items, Users
import random, string

app = Flask(__name__)

engine = create_engine("sqlite:///catalog.db",
                        connect_args={"check_same_thread": False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route("/")
@app.route("/catalog")
def showCatalog():
    MAX_RESULTS = 10
    categories = session.query(Categories).order_by(Categories.name).all()
    items = session.query(Items.title, Categories.name.label("category_name")) \
        .join(Items.category) \
        .order_by(Items.id.desc()) \
        .limit(MAX_RESULTS) \
        .all()
    return render_template("catalog.html", categories = categories,
                            items = items, category_name = None)

@app.route("/catalog/<category_name>")
@app.route("/catalog/<category_name>/items")
def showAllItems(category_name):
    categories = session.query(Categories).order_by(Categories.name).all()
    category = session.query(Categories) \
        .filter(Categories.name.ilike(category_name.lower())) \
        .first()
    if not category:
        flash("Category not found")
        return redirect(url_for("showCatalog"))

    items = session.query(Items) \
        .filter_by(category_id = category.id) \
        .order_by(Items.title) \
        .all()
    return render_template("catalog.html", categories = categories,
                            items = items, category_name = category.name)

@app.route("/catalog/<category_name>/<item_name>")
def showItem(category_name, item_name):
    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        return render_template("item.html", category_name = category_name,
                                item = item)
    else:
        return return_value

@app.route("/catalog/new", defaults={"category_name": None},
            methods=["GET", "POST"])
@app.route("/catalog/<category_name>/new", methods=["GET", "POST"])
def addItem(category_name):
    categories = session.query(Categories).order_by(Categories.name).all()

    if request.method == "POST":
        if request.form['title'] \
        and request.form['description'] \
        and request.form['category']:
            # TODO: Usar ID real do usuário logado
            itemToAdd = Items(title=request.form['title'],
                            description=request.form['description'],
                            category_id=request.form['category'],
                            user_id=1)
            try:
                session.add(itemToAdd)
                session.commit()
                flash("New item created")
                if category_name:
                    return redirect(url_for("showAllItems",
                                            category_name = category_name))
                else:
                    return redirect(url_for("showCatalog"))
            except IntegrityError:
                session.rollback()
                flash("Item '%s' already exists in selected category." %
                    request.form['title'])
                return render_template("newitem.html",
                                        category_name = category_name,
                                        categories = categories,
                                        item = request.form.to_dict())
        else:
            flash("There is missing data")
            return render_template("newitem.html",
                                    category_name = category_name,
                                    categories = categories,
                                    item = request.form.to_dict())

    if category_name:
        category = session.query(Categories) \
            .filter(Categories.name.ilike(category_name.lower())) \
            .first()
        if not category:
            return redirect(url_for("addItem"))
    return render_template("newitem.html", category_name = category_name,
                            categories = categories)

@app.route("/catalog/<category_name>/<item_name>/edit", methods=["GET", "POST"])
def editItem(category_name, item_name):
    if request.method == "POST":
        flash("Item edited")
        return redirect(url_for("showItem", category_name = category_name,
                                item_name = item_name))

    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        categories = session.query(Categories).order_by(Categories.name).all()
        return render_template("edititem.html", category_name = category_name,
                                categories = categories, item = item)
    else:
        return return_value

@app.route("/catalog/<category_name>/<item_name>/delete", methods=["GET", "POST"])
def deleteItem(category_name, item_name):
    if request.method == "POST":
        flash("Item deleted")
        return redirect(url_for("showAllItems", category_name = category_name))

    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        categories = session.query(Categories).order_by(Categories.name).all()
        return render_template("deleteitem.html", category_name = category_name,
                                item = item)
    else:
        return return_value

def checkCategoryAndItem(category_name, item_name):
    category = session.query(Categories) \
        .filter(Categories.name.ilike(category_name.lower())) \
        .first()
    if not category:
        flash("Category not found")
        return None, redirect(url_for("showCatalog"))

    item = session.query(Items) \
        .filter_by(category_id = category.id) \
        .filter(Items.title.ilike(item_name.lower())) \
        .first()

    if not item:
        flash("Item not found in '%s'" % category.name)
        return None, redirect(url_for("showAllItems",
                                    category_name = category.name.lower()))

    return item, None

# Endpoints para a API

@app.route("/catalog.json")
def showCatalogJSON():
    categories = session.query(Categories).order_by(Categories.name).all()

    categories_list = []
    for category in categories:
        categories_list.append(getCategoryEntry(category))

    return jsonify(Categories = categories_list)

@app.route("/catalog/<category_name>.json")
def showAllItemsJSON(category_name):
    category = session.query(Categories) \
        .filter(Categories.name.ilike(category_name.lower())) \
        .first()
    if not category:
        return jsonify({"error": "Category not found"})

    return jsonify(Category = getCategoryEntry(category))

@app.route("/catalog/latest.json")
def showLatestItemsJSON():
    max_results = request.args.get("limit")
    if not max_results:
        max_results = 10

    items = session.query(Items.title,
                        Items.description,
                        Categories.name.label("category_name"),
                        Users.name.label("creator")) \
        .join(Items.category, Items.user) \
        .order_by(Items.id.desc()) \
        .limit(max_results) \
        .all()

    items_list = []
    for i in items:
        items_list.append({
            "title": i.title,
            "description": i.description,
            "category_name": i.category_name,
            "creator": i.creator,
        })

    return jsonify(Latest = items_list)

def getCategoryEntry(category):
    category_entry = {"name": category.name}
    items = session \
        .query(Items.title, Items.description, Users.name.label("creator")) \
        .join(Items.user) \
        .filter(Items.category_id == category.id) \
        .order_by(Items.title) \
        .all()

    if len(items):
        items_list = []
        for i in items:
            items_list.append({
                "title": i.title,
                "description": i.description,
                "creator": i.creator,
            })

        category_entry["items"] = items_list

    return category_entry


if __name__ == "__main__":
    app.debug = True
    app.config["SECRET_KEY"] = "" \
        .join(random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    app.run(host="0.0.0.0", port=8000)
