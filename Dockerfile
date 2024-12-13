# ベースイメージの指定
FROM python:3.9

# 作業ディレクトリの設定
WORKDIR /usr/src/

# 必要なファイルのコピー
COPY ./requirements.txt /usr/src/requirements.txt

RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0


# 仮想環境の作成
RUN python -m venv /usr/src/venv

# 仮想環境の有効化と依存関係のインストール
RUN /usr/src/venv/bin/pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY ./apps /usr/src/apps
COPY ./local.sqlite /usr/src/local.sqlite
COPY ./best11month.pt /usr/src/best11month.pt

# 環境変数の設定
ENV FLASK_APP="apps.app:create_app('local')"
ENV IMAGE_URL="/storage/images/"

# ポートの公開
EXPOSE 8080

# コンテナ内で実行するコマンド（仮想環境を使う）
CMD ["/usr/src/venv/bin/gunicorn", "-b", "0.0.0.0:8080", "apps.app:create_app('local')"]
