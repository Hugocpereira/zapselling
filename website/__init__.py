from flask import Flask, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
import base64
# from jinja2 import Markup  # Adicionado este import

DB_NAME = 'database.db'
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'zapselling'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = ['png', 'jpg', 'jpeg', 'gif', 'mp3', 'mp4', 'doc', 'xlsx', 'pdf', 'txt', 'xlsm', 'ods']
    TEMPORARY_GARBAGE_TIMEOUT = 300
    app.jinja_env.filters['b64encode'] = b64encode

    migrate = Migrate(app, db)
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Post

    create_database(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app, db):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created database')

def allowed_file(filename, config):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config['ALLOWED_EXTENSIONS']

def b64encode(value):
    return base64.b64encode(value).decode('utf-8')
