from datetime import datetime
from apps.app import db

class UserImage(db.Model):
    __tablename__ = "user_images"
    __table_args__ = {'extend_existing': True}  # これを追加
    id = db.Column(db.Integer, primary_key=True)
    #user_idはusersテーブルのidカラムを外部キーとして設定する
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    image_path = db.Column(db.String)
    is_detected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    detected_at = db.Column(db.DateTime, nullable=True) #検出時間
    point = db.Column(db.Integer, default=0)

    tags = db.relationship('UserImageTag', backref='user_image', lazy=True)

class UserImageTag(db.Model):
    __tablename__ = "user_image_tags"
    id = db.Column(db.Integer, primary_key=True)
    user_image_id = db.Column(db.String, db.ForeignKey("user_images.id"))
    tag_name = db.Column(db.String)
    note = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    category = db.Column(db.String, nullable=True)

    @staticmethod
    def count_tag_for_user(user_id, tag_name):
        return db.session.query(UserImageTag).join(UserImage).filter(UserImage.user_id == user_id, UserImageTag.tag_name == tag_name).count()

    @staticmethod
    def check_achievement_for_tag(user_id, tag_name, target_count):
        tag_count = UserImageTag.count_tag_for_user(user_id, tag_name)
        return tag_count >= target_count, tag_count

    
    @staticmethod
    def count_by_category(user_id, category):
        #特定のユーザーの画像をカテゴリごとにカウント
        return db.session.query(UserImageTag).join(UserImage).filter(UserImage.user_id == user_id,UserImageTag.category == category).count()

class DailyMission(db.Model):
    __tablename__ = "dailymission"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date = db.Column(db.Date, nullable=False, default=datetime.today)
    breakfast = db.Column(db.Boolean, default=False)  # 朝食
    lunch = db.Column(db.Boolean, default=False)      # 昼食
    dinner = db.Column(db.Boolean, default=False)     # 夕食

    def all_meals_completed(self):
        """朝昼夜すべて食べたかを判定"""
        return self.breakfast and self.lunch and self.dinner
    
    @staticmethod
    def check_daily_meals_completed(user_id, date):
        """特定の日付の朝昼夜をすべて食べたか判定"""
        categories = {"breakfast", "lunch", "dinner"}
        recorded_categories = (
            db.session.query(UserImageTag.category)
            .join(UserImage)
            .filter(
                UserImage.user_id == user_id,
                db.func.date(UserImage.created_at) == date,
            )
            .distinct()
        )
        recorded_categories_set = {row[0] for row in recorded_categories}
        return categories.issubset(recorded_categories_set)




