from pathlib import Path
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from apps.config import config
from flask_login import LoginManager
import logging
import os

# SQLAlchemyをインスタンス化する
db = SQLAlchemy()
csrf = CSRFProtect()

# LoginManagerをインスタンス化する
login_manager = LoginManager()
# login_view属性に未ログイン時にリダイレクトするエンドポイントを指定する
login_manager.login_view = "auth.signup"
# login_message属性にログイン後に表示するメッセージを指定する
login_manager.login_message = ""

# Flaskアプリケーションファクトリー
def create_app(config_key):
    app = Flask(__name__)  # Flaskインスタンス生成
    app.config.from_object(config[config_key])

    # Flask-Mailの設定
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '')

    # ログレベルをINFOに設定（本番環境向け）
    app.logger.setLevel(logging.INFO)

    # アプリのコンフィグ設定
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', '2AZSMss3p5QPbcY2hBsJ'),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            'DATABASE_URL',
            f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=False,  # デバッグ用ログを無効化（本番環境向け）
        WTF_CSRF_SECRET_KEY=os.getenv('WTF_CSRF_SECRET_KEY', 'AuwzyszU5sugKN7KZs6f'),
    )

    # カスタムエラー画面を登録
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    # 拡張機能をアプリに登録
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)

    # Blueprintを登録
    from apps.crud import views as crud_views
    app.register_blueprint(crud_views.crud, url_prefix="/crud")
    from apps.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix="/auth")
    from apps.detector import views as dt_views
    app.register_blueprint(dt_views.dt)

    return app


# 登録したエンドポイント名の関数を作成し、404や500が発生した際に指定したHTMLを返す
def page_not_found(e):
    """404 Not Found"""
    return render_template("404.html"), 404


def internal_server_error(e):
    """500 Internal Server Error"""
    return render_template("500.html"), 500


# Cloud Runでのエントリーポイント
# Flask アプリインスタンスを明示的に指定
app = create_app('production')  # 必要に応じて 'production' を他の設定に変更

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
