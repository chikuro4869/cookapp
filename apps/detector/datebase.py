from apps.app import db
db.session.execute('DROP TABLE IF EXISTS users')  # 'users' テーブルを削除
db.session.commit()  # コミットして変更を反映