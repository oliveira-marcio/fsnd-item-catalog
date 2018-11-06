#!/usr/bin/env python2
# coding: utf-8

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import Base, Categories, Items, Users
from flask import session as login_session
from utils import CLIENT_ID, doGoogleSignIn, doGoogleSignOut, doDisconnect, getSecretKey

app = Flask(__name__)

engine = create_engine("sqlite:///catalog.db",
                        connect_args={"check_same_thread": False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route("/gconnect", methods=["POST"])
def gconnect():
    return doGoogleSignIn(app, session)

@app.route("/gdisconnect")
def gdisconnect():
    return doGoogleSignOut()

@app.route("/disconnect")
def disconnect():
    return doDisconnect(redirect(url_for("showCatalog")))

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

    if "username" not in login_session:
        return render_template("public_catalog.html", categories = categories,
                                items = items, category_name = None,
                                STATE = app.config["SECRET_KEY"],
                                CLIENT_ID = CLIENT_ID,
                                routeCallBack = "showCatalog")
    else:
        return render_template("catalog.html", categories = categories,
                                items = items, category_name = None,
                                routeCallBack = "showCatalog")

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

    if "username" not in login_session:
        return render_template("public_catalog.html", categories = categories,
                                items = items, category_name = category.name,
                                STATE = app.config["SECRET_KEY"],
                                CLIENT_ID = CLIENT_ID,
                                routeCallBack = "showAllItems")
    else:
        return render_template("catalog.html", categories = categories,
                                items = items, category_name = category.name,
                                routeCallBack = "showAllItems")

@app.route("/catalog/<category_name>/<item_name>")
def showItem(category_name, item_name):
    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        # TODO: Checar se o usuário é o criador do item para poder editar/deletar
        if "username" not in login_session:
            return render_template("public_item.html", category_name = category_name,
                                    item = item,
                                    STATE = app.config["SECRET_KEY"],
                                    CLIENT_ID = CLIENT_ID,
                                    routeCallBack = "showItem")
        else:
            return render_template("item.html", category_name = category_name,
                                    item = item, routeCallBack = "showItem")
    else:
        return return_value

@app.route("/catalog/new", defaults={"category_name": None},
            methods=["GET", "POST"])
@app.route("/catalog/<category_name>/new", methods=["GET", "POST"])
def addItem(category_name):
    # TODO: Checar se o usuário está autenticado para poder criar
    categories = session.query(Categories).order_by(Categories.name).all()

    if request.method == "POST":
        return doDatabaseWrite(categories, category_name, request.form.to_dict())

    # Necessário espeficar um objeto item para o template
    item = {}
    if category_name:
        category = session.query(Categories) \
            .filter(Categories.name.ilike(category_name.lower())) \
            .first()
        if not category:
            return redirect(url_for("addItem"))
        item["category_id"] = category.id

    return render_template("newitem.html",
                            item = item,
                            categories = categories,
                            previous_category = category_name)

@app.route("/catalog/<category_name>/<item_name>/edit", methods=["GET", "POST"])
def editItem(category_name, item_name):
    # TODO: Checar se o usuário está autenticado para poder editar
    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        categories = session.query(Categories).order_by(Categories.name).all()
        if request.method == "POST":
            return doDatabaseWrite(categories, category_name, request.form.to_dict(), item)

        return render_template("edititem.html",
                                previous_category = category_name,
                                previous_item = item.title,
                                categories = categories,
                                item = item)
    else:
        return return_value

def doDatabaseWrite(categories, previous_category, user_data, item = None):
    if item:
        form_name = "edititem.html"
        message = "Item edited"
        isInsert = False
    else:
        # TODO: Usar ID real do usuário logado
        item = Items(title = None,
                    description = None,
                    category_id = None,
                    user_id = 1)
        form_name = "newitem.html"
        message = "New item created"
        isInsert = True

    if user_data["title"] \
    and user_data["description"] \
    and user_data["category_id"]:
        item.title = user_data["title"]
        item.description = user_data["description"]
        item.category_id = user_data["category_id"]

        try:
            session.add(item)
            session.commit()
            flash(message)

            category_name = session.query(Categories) \
                .filter_by(id = user_data["category_id"]) \
                .first().name

            if isInsert:
                return redirect(url_for("showAllItems",
                                        category_name = category_name))
            else:
                return redirect(url_for("showItem", category_name = category_name,
                                        item_name = user_data["title"]))
        except IntegrityError:
            session.rollback()
            flash("Item '%s' already exists in selected category." %
                user_data["title"])
            return render_template(form_name,
                                    categories = categories,
                                    item = user_data,
                                    previous_category = previous_category,
                                    previous_item = item.title)
    else:
        flash("There is missing data")
        return render_template(form_name,
                                categories = categories,
                                item = user_data,
                                previous_category = previous_category,
                                previous_item = item.title)

@app.route("/catalog/<category_name>/<item_name>/delete", methods=["GET", "POST"])
def deleteItem(category_name, item_name):
    # TODO: Checar se o usuário está autenticado para poder deletar
    item, return_value = checkCategoryAndItem(category_name, item_name)

    if item:
        if request.method == "POST":
            session.delete(item)
            session.commit()
            flash("Item deleted")
            return redirect(url_for("showAllItems", category_name = category_name))

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
    app.config["SECRET_KEY"] = getSecretKey()
    app.run(host="0.0.0.0", port=8000)
