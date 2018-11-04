#!/usr/bin/env python2
# coding: utf-8

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_setup import Base, Categories, Items, Users
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open("client_secrets.json", "r").read())["web"]["client_id"]
APPLICATION_NAME = "Item Catalog Application"

engine = create_engine("sqlite:///catalog.db",
                        connect_args={"check_same_thread": False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route("/login")
def showLogin():
    state = app.config["SECRET_KEY"]
    login_session["state"] = state
    return render_template("login.html", STATE=state, CLIENT_ID = CLIENT_ID)

@app.route("/gconnect", methods=["POST"])
def gconnect():
    # Validate state token
    if request.args.get("state") != login_session["state"]:
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets("client_secrets.json", scope="")
        oauth_flow.redirect_uri = "postmessage"
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps("Failed to upgrade the authorization code."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s"
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, "GET")[1])
    # If there was an error in the access token info, abort.
    if result.get("error") is not None:
        response = make_response(json.dumps(result.get("error")), 500)
        response.headers["Content-Type"] = "application/json"
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token["sub"]
    if result["user_id"] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers["Content-Type"] = "application/json"
        return response

    # Verify that the access token is valid for this app.
    if result["issued_to"] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers["Content-Type"] = "application/json"
        return response

    stored_access_token = login_session.get("access_token")
    stored_gplus_id = login_session.get("gplus_id")
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user is already connected."),
                                 200)
        response.headers["Content-Type"] = "application/json"
        return response

    # Store the access token in the session for later use.
    login_session["access_token"] = credentials.access_token
    login_session["gplus_id"] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {"access_token": credentials.access_token, "alt": "json"}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session["username"] = data["name"]
    login_session["picture"] = data["picture"]
    login_session["email"] = data["email"]
    # ADD PROVIDER TO LOGIN SESSION
    login_session["provider"] = "google"

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session["user_id"] = user_id

    output = ""
    output += "<h1>Welcome, "
    output += login_session["username"]
    output += "!</h1>"
    output += "<img src='"
    output += login_session["picture"]
    output += "' style = 'width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;'>"
    flash("you are now logged in as %s" % login_session["username"])
    print "done!"
    return output

@app.route("/gdisconnect")
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get("access_token")
    if access_token is None:
        response = make_response(
            json.dumps("Current user not connected."), 401)
        response.headers["Content-Type"] = "application/json"
        return response
    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
    h = httplib2.Http()
    result = h.request(url, "GET")[0]
    if result["status"] == "200":
        response = make_response(json.dumps("Successfully disconnected."), 200)
        response.headers["Content-Type"] = "application/json"
        return response
    else:
        response = make_response(json.dumps("Failed to revoke token for given user.", 400))
        response.headers["Content-Type"] = "application/json"
        return response

# Disconnect based on provider
@app.route("/disconnect")
def disconnect():
    if "provider" in login_session:
        if login_session["provider"] == "google":
            gdisconnect()
            del login_session["gplus_id"]
            del login_session["access_token"]
        del login_session["username"]
        del login_session["email"]
        del login_session["picture"]
        del login_session["user_id"]
        del login_session["provider"]
        flash("You have successfully been logged out.")
        return redirect(url_for("showCatalog"))
    else:
        flash("You were not logged in")
        return redirect(url_for("showCatalog"))

def createUser(login_session):
    newUser = Users(name=login_session["username"], email=login_session[
                   "email"], picture=login_session["picture"])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(email=login_session["email"]).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(Users).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except:
        return None

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
        return render_template("publiccatalog.html", categories = categories,
                                items = items, category_name = None)
    else:
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
    app.config["SECRET_KEY"] = "" \
        .join(random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    app.run(host="0.0.0.0", port=8000)
