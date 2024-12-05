from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import length

#ユーザー編集フォームクラス
class Edit(FlaskForm):
    tag_name = StringField("料理名",validators=[length(max=30, message="30文字以内で入力してください。"),],) #タグ名を設定する
    submit = SubmitField("更新") #ユーザーフォームsubmit文言を設定する