from pathlib import Path
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from apps.config import config
from flask_login import LoginManager
import logging
import os

#SQLAlchemyをインスタンス化する
db = SQLAlchemy()
csrf = CSRFProtect()

#LoginManagerをインスタンス化する
login_manager=LoginManager()
#login_view属性に未ログイン時にリダイレクトするエンドポイントを指定する
login_manager.login_view = "auth.signup"
#login_message属性にログイン後に表示するメッセージを指定する
#ここでは何も表示しないよう空を指定する
login_manager.login_message = ""

#create_app関数を作成する
def create_app(config_key):
    app = Flask(__name__) #Flaskインスタンス生成
#config_keyにマッチする環境のコンフィグクラスを読み込む
    app.config.from_object(config[config_key])

    # Flask-Mailの設定
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # ログレベルをDEBUGに設定
    app.logger.setLevel(logging.DEBUG)

    #アプリのコンフィグ設定する
    app.config.from_mapping(
        SECRET_KEY = "2AZSMss3p5QPbcY2hBsJ",
        SQLALCHEMY_DATABASE_URI =
        f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        #SQLをコンソールログに出力する設定
        SQLALCHEMY_ECHO=True,
        WTF_CSRF_SECRET_KEY = "AuwzyszU5sugKN7KZs6f",)

    #カスタムエラー画面を登録する
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    csrf.init_app(app)
    db.init_app(app) #SQLAlchemyとアプリを連携する
    Migrate(app, db) #Migrateとアプリを連携する

    login_manager.init_app(app) #login_managerをアプリケーションと連携する

    from apps.crud import views as crud_views #crudパッケージからviewsをimportする
    app.register_blueprint(crud_views.crud, url_prefix="/crud") #viewsのcrudをアプリへ登録する
    from apps.auth import views as auth_views #authパッケージからviewsをimportする
    app.register_blueprint(auth_views.auth, url_prefix="/auth") #viewsのauthをアプリへ登録する
    from apps.detector import views as dt_views #detectorパッケージからviewsをimportする
    app.register_blueprint(dt_views.dt) #viewsのdtをアプリへ登録する
    return app



#登録したエンドポイント名の関数を作成し、404や500が発生した際に指定したHTMLを返す
def page_not_found(e):
    """404 Not Found"""
    return render_template("404.html"), 404

def internal_server_error(e):
    """500 Internal Server Error"""
    return render_template("500.html"), 500


