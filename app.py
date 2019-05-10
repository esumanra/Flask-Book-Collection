import os
from flask import Flask
from flask import render_template, redirect, url_for, g
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_oidc import OpenIDConnect
from okta import UsersClient

project_dir = os.path.dirname(os.path.abspath(__file__))
print(project_dir)
database_file = "sqlite:///{}".format(
    os.path.join(project_dir, "book_collection.db"))

app = Flask(__name__)
# Databse configurations
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
# Okta Auth Configuration
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["SECRET_KEY"] = "{{ LONG_RANDOM_STRING }}"
app.config["OIDC_ID_TOKEN_COOKIE_NAME"] = "oidc_token"
oidc = OpenIDConnect(app)
okta_client = UsersClient("{okta url}",
                          "{okta_token}")

db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    genre = db.Column(db.String(250))


@app.before_request
def before_request():
    if oidc.user_loggedin:
        g.user = okta_client.get_user(oidc.user_getfield("sub"))
    else:
        g.user = None


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for(".showBooks"))


@app.route("/logout")
def logout():
    oidc.logout()
    return redirect(url_for(".index"))


# Home page
@app.route("/")
def index():
    return render_template('index.html')


# landing page that will display all the books in our database
@app.route('/books')
# @oidc.require_login
def showBooks():
    books = Book.query.all()
    print(books)
    return render_template("books.html", books=books)


# This will let us Create a new book and save it in our database
@app.route('/books/new/', methods=['GET', 'POST'])
# @oidc.require_login
def newBook():
    if request.method == 'POST':
        print(request.form['author'])
        newBook = Book(
            title=request.form['name'], author=request.form['author'], genre=request.form['genre'])
        db.session.add(newBook)
        db.session.commit()
        return redirect(url_for('showBooks'))
    else:
        return render_template('newBook.html')


# This will let us Update our books and save it in our database
@app.route("/books/<int:book_id>/edit/", methods=['GET', 'POST'])
# @oidc.require_login
def editBook(book_id):
    editedBook = Book.query.filter_by(id=book_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBook.title = request.form['name']
            db.session.commit()
            return redirect(url_for('showBooks'))
    else:
        return render_template('editBook.html', book=editedBook)


# This will let us Delete our book
@app.route('/books/<int:book_id>/delete/', methods=['GET', 'POST'])
# @oidc.require_login
def deleteBook(book_id):
    bookToDelete = Book.query.filter_by(id=book_id).one()
    if request.method == 'POST':
        db.session.delete(bookToDelete)
        db.session.commit()
        return redirect(url_for('showBooks'))
    else:
        return render_template('deleteBook.html', book=bookToDelete)


if __name__ == '__main__':
    app.debug = True
    app.run("localhost", 5000)
