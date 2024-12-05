from apps.app import db
from apps.crud.models import User
from apps.detector.models import UserImage, UserImageTag,DailyMission
from flask import Blueprint,render_template, current_app, send_from_directory, redirect,url_for, flash, request
from flask_login import current_user, login_required
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError
import uuid 
from pathlib import Path
from apps.detector.forms import UploadImageForm, DetectorForm, DeleteForm
from apps.detector.editform import Edit
#yolo検出関連
import random,cv2
from ultralytics import YOLO
import numpy as np
from datetime import datetime #検出時間
from apps.detector.carories import tag_info

#dtアプリケーションを使ってエンドポイントを作成する
dt = Blueprint("detector", __name__, template_folder="templates")

@dt.route("/")
def index():
    # 現在の時刻を取得
    now = datetime.now()
    nowhour = now.hour
    formatted_now = now.strftime('%Y年%m月%d日%H時')
    formatted_today = now.strftime('%m月%d日%H時%M分')

    # ページ番号をURLパラメータから取得（デフォルトは1ページ目）
    page = request.args.get("page", 1, type=int)
    per_page = 3  # 1ページあたりの投稿数

    # 並び替え順序をURLパラメータから取得（デフォルトは降順 "desc"）
    sort_order = request.args.get("sort", "desc")
    
    # ソート順に応じてクエリを作成
    query = db.session.query(User, UserImage).join(UserImage).filter(User.id == UserImage.user_id)
    if sort_order == "asc":
        query = query.order_by(UserImage.id.asc())  # 昇順
    else:
        query = query.order_by(UserImage.id.desc())  # 降順
        
    # ページネーションを適用
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    user_images = pagination.items

    # タグ一覧を取得する
    user_image_tag_dict = {}
    for user_image in user_images:
        # 画像に紐づくタグ一覧を取得
        user_image_tags = (db.session.query(UserImageTag)
                           .filter(UserImageTag.user_image_id == user_image.UserImage.id)
                           .all())
        user_image_tag_dict[user_image.UserImage.id] = user_image_tags
        # 時間に基づいてポイントを加算

    # フォームをインスタンス化
    detector_form = DetectorForm() 
    delete_form = DeleteForm()  # 削除フォーム

    return render_template(
        "detector/index.html",
        user_images=user_images,
        user_image_tag_dict=user_image_tag_dict,  # タグ一覧をテンプレートに渡す
        detector_form=detector_form,  # 物体検知フォームをテンプレートに渡す
        delete_form=delete_form,  # 削除フォームをテンプレートに渡す
        sort_order  = sort_order ,
        nowhour = nowhour,
        now = now ,
        formatted_now  = formatted_now ,
        formatted_today = formatted_today ,
        pagination=pagination,  # ページネーションオブジェクトを渡す
    )

        
@dt.route("/images/file/<path:filename>")
def image_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)



@dt.route("/upload", methods=["GET", "POST"])
@login_required
def upload_image():
    form = UploadImageForm()
    if form.validate_on_submit():
        file  = form.image.data #アップロードされた画像ファイルを取得
        ext = Path(file.filename).suffix #ファイルのファイル名と拡張子を取得
        image_uuid_file_name = str(uuid.uuid4()) + ext #ファイル名をuuidに変換
        #画像を保存する
        image_path = Path(current_app.config["UPLOAD_FOLDER"], image_uuid_file_name)
        file.save(image_path)
        #DBに保存する
        user_image = UserImage(user_id = current_user.id, image_path=image_uuid_file_name)
        db.session.add(user_image)
        db.session.commit()

        # 物体検知を実行
        try:
            target_image_path = Path(current_app.config["UPLOAD_FOLDER"], user_image.image_path)
            tags, detected_image_file_name = exec_detec(target_image_path)

            # 検知結果をデータベースに保存
            save_detected_image_tags(user_image, tags, detected_image_file_name)

            # 物体検知が成功した場合にフラッシュメッセージを設定
            flash("検知終了しました。", "success")

        except SQLAlchemyError as e:
            flash("物体検知処理でエラーが発生しました。")
            db.session.rollback()
            current_app.logger.error(e)  # エラーログ出力
        except Exception as e:
            flash("予期しないエラーが発生しました。")
            current_app.logger.error(e)  # エラーログ出力
            return redirect(url_for("detector.index"))

        return redirect(url_for("detector.index"))
    return render_template("detector/upload.html", form=form)

def make_color(labels):
    color = [[random.randint(0,255) for _ in range(3)] for _ in labels]
    color = random.choice(color) #枠線の色をランダムに決定
    return color

def make_line(result_image):
    line = round(0.002 * max(result_image.shape[0:2])) +1 #枠線を作成
    return line

def draw_lines(c1, c2, result_image, line, color):
    cv2.rectangle(result_image, c1, c2, color, thickness=line) ##四角形の枠線を画像に追記
    return cv2

def draw_texts(result_image, line, c1, c2, color, labels, label):
    display_txt = f"{labels[label]}" 
    font = max(line - 1, 1)
    t_size = cv2.getTextSize(display_txt, 0, fontScale=line / 3, thickness=font)[0]
    c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
    cv2.rectangle(result_image, c1, c2, color, -1)
    #検知したテキストラベルを画像に追記
    cv2.putText(result_image,display_txt,(c1[0], c1[1] - 2),0,line / 3,[255,255,255],thickness=font,lineType=cv2.LINE_AA,)
    return cv2

def exec_detec(target_image_path):
    labels = current_app.config["LABELS"]# ラベルの読み込み
    image = Image.open(target_image_path)# 画像の読み込み
    model = YOLO(Path(current_app.root_path, "detector", 'best11month.pt'))# 学習済みモデルの読み込み
    results = model(image)# 推論の実行
    tags = []
    result_image = np.array(image.copy())

    # 検出結果を解析
    for result in results:
        for r in result.boxes:
            if r.conf.item() > 0.5 and labels[int(r.cls.item())] not in tags:
                color = make_color(labels) # 枠線の色の決定
                line = make_line(result_image) # 枠線の作成
                # 検知画像の枠線とテキストラベルの枠線の位置情報
                c1 = (int(r.xyxy[0][0].item()), int(r.xyxy[0][1].item()))
                c2 = (int(r.xyxy[0][2].item()), int(r.xyxy[0][3].item()))
                draw_lines(c1, c2, result_image, line, color) # 画像に枠線を追記
                # 画像にテキストラベルを追記
                draw_texts(result_image, line, c1, c2, color, labels, int(r.cls.item()))
                tags.append(labels[int(r.cls.item())])
    # 検知後の画像ファイル名を生成
    detected_image_file_name = str(uuid.uuid4()) + ".jpg" 
    # 画像コピー先パスを取得する
    detected_image_file_path = str(Path(current_app.config["UPLOAD_FOLDER"], detected_image_file_name))
    # 変換後の画像ファイルを保存先へコピーする
    cv2.imwrite(detected_image_file_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))
    return tags, detected_image_file_name
    
def save_detected_image_tags(user_image, tags, detected_image_file_name):
    #検知画像の保存先パスをＤＢに保存する
    user_image.image_path = detected_image_file_name
    #検知フラグをtrueにする
    user_image.is_detected = True
    user_image.detected_at = datetime.now()  # 検出時刻を記録
    db.session.add(user_image)
    #user_images_tagsレコードを作成する
    for tag in tags:
        user_image_tag = UserImageTag(user_image_id=user_image.id, tag_name=tag)
        db.session.add(user_image_tag)
        db.session.commit()

@dt.route("/detect/<string:image_id>", methods=["POST"])
@login_required
def detect(image_id):
    #user_imagesテーブルからレコードを取得する
    user_image=(db.session.query(UserImage).filter(UserImage.id == image_id).first())
    if user_image is None:
        flash("物体検知対象の画像が存在しません")
        return redirect(url_for("detector/index"))
    #物体検知対象の画像パスを取得する
    target_image_path = Path(current_app.config["UPLOAD_FOLDER"], user_image.image_path)
    #物体検知を実行してタグと変換後の画像パスを取得する
    tags, detected_image_file_name = exec_detec(target_image_path)
    try:
        #データベースにタグと変換後の画像パス情報を保存する
        save_detected_image_tags(user_image, tags, detected_image_file_name)
    except SQLAlchemyError as e:
        flash("物体検知処理でエラーが起きました")
        db.session.rollback() #ロールバックする
        current_app.logger.error(e) #エラーログ出力
        return redirect(url_for("detector.index"))
    return redirect(url_for("detector.index"))

@dt.route("/images/delete/<string:image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    try:
        #user_image_tagsテーブルからレコードを削除する
        db.session.query(UserImageTag).filter(UserImageTag.user_image_id == image_id).delete()
        #user_imagesテーブルからレコードを削除する
        db.session.query(UserImage).filter(UserImage.id == image_id).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        flash("画像削除処理でエラーが発生しました。")
        current_app.logger.error(e) #エラーログ出力
        db.session.rollback()
    return redirect(url_for("detector.index"))

@dt.route('/edit_image/<int:image_id>', methods=['GET', 'POST'])
def edit_image(image_id):
    form=Edit()
    user_image = UserImage.query.get_or_404(image_id)
    # タグ情報を取得するために、UserImageTagから関連するタグを取得
    user_image_tags = UserImageTag.query.filter_by(user_image_id=user_image.id).all()
    existing_note = user_image_tags[0].note if user_image_tags else ''  # 既存のメモを取得
    # GETリクエストの場合、既存のメモを取得する
    if request.method == 'POST':
        new_note = request.form.get('note') #新しいメモを保存する
        # タグにメモを追加
        if user_image_tags:
            user_image_tags[0].note = new_note
        else:
            print("No tags found for this image.")

        new_tags = request.form.get('tag_name')
        if new_tags:
            new_tags=new_tags.split(',')
            UserImageTag.query.filter_by(user_image_id=user_image.id).delete() # 既存のタグを削除する処理
            # 新しいタグを追加
            for tag_name in new_tags:
                tag_name = tag_name.strip()  # タグ名の前後の空白を削除
                if tag_name:  # タグ名が空でない場合のみ追加
                    new_tag = UserImageTag(user_image_id=user_image.id, tag_name=tag_name)
                    db.session.add(new_tag)
        db.session.commit()
        #flash('タグが更新されました。', 'success')
        return redirect(url_for('detector.index'))
    return render_template('detector/edit.html', user_image_tags=[tag.tag_name for tag in user_image_tags], image_id=image_id, form=form, note=existing_note)

@dt.route("/images/search", methods=["GET"])
def search():
    user_images = db.session.query(User, UserImage).join(UserImage, User.id == UserImage.user_id)#画像一覧を取得
    search_text = request.args.get("search") #GETパラメータから検索ワードを取得
    user_images_tag_dict = {}
    filtered_user_images = []
    #user_imagesをループしuser_imagesに紐づくタグ情報を検索する
    for user_image in user_images:
        if not search_text :  #検索ワードが空の場合はすべてのタグを取得する
            #タグ一覧を取得する
            user_image_tags = (db.session.query(UserImageTag).filter(UserImageTag.user_image_id == user_image.UserImage.id).all())
        else:
            #検索ワードで絞り込んだタグを取得する
            user_image_tags = (db.session.query(UserImageTag).filter(UserImageTag.user_image_id == user_image.UserImage.id).filter(UserImageTag.tag_name.like("%" + search_text + "%")).all())
        #タグが見つからなかったら画像を返さない
        if not user_image_tags:
            continue
        #タグがある場合はタグ情報を取得しなおす
        user_image_tags = (db.session.query(UserImageTag).filter(UserImageTag.user_image_id == user_image.UserImage.id).all())

        #user_image_id をキーとする辞書にタグ情報をセットする
        user_images_tag_dict[user_image.UserImage.id] = user_image_tags

        #絞り込み結果のuser_image情報を配列セットする
        filtered_user_images.append(user_image)

    delete_form = DeleteForm()
    detector_form = DetectorForm()

    return render_template(
        "detector/index.html",
        #絞り込んだuser_images配列を返す
        user_images=filtered_user_images,
        #画像に紐づくタグ一覧の辞書を渡す
        user_image_tag_dict=user_images_tag_dict,
        delete_form=delete_form,
        detector_form=detector_form, )

@dt.errorhandler(404)
def page_not_found(e):
    return render_template("detector/404.html"),404


#指定されたユーザーのアチーブメント達成状況を取得し、ページに表示する
@dt.route('/achievements/')
@login_required
def achievements():
    user_id = current_user.id  # 現在のユーザーIDを取得
    # 確認したいタグ名のリスト
    tag_names = ['rice', 'eels on rice', 'pilaf', 'chicken-n-egg on rice', 'pork cutlet on rice', 'beef curry', 'sushi', 'chicken rice', 'fried rice', 'tempura bowl', 'bibimbap', 'toast', 'croissant', 'roll bread', 'raisin bread', 'chip butty', 'hamburger', 'pizza', 'sandwiches', 'udon noodle','tempura udon','soba noodle', 'ramen noodle', 'beef noodle', 'tensin noodle', 'fried noodle', 'spaghetti', 'Japanese-style pancake', 'takoyaki', 'gratin','sauteed vegetables', 'croquette', 'grilled eggplant', 'sauteed spinach', 'vegetable tempura', 'miso soup', 'potage', 'sausage','oden', 'omelet', 'ganmodoki', 'jiaozi', 'stew', 'teriyaki grilled fish', 'fried fish', 'grilled salmon', 'salmon meuniere', 'sashimi','grilled pacific saury ', 'sukiyaki', 'sweet and sour pork', 'lightly roasted fish', 'steamed egg hotchpotch', 'tempura', 'fried chicken','sirloin cutlet', 'nanbanzuke', 'boiled fish','seasoned beef with potatoes', 'hambarg steak', 'beef steak', 'dried fish', 'ginger pork saute','spicy chili-flavored tofu', 'yakitori', 'cabbage roll', 'rolled omelet', 'egg sunny-side up', 'fermented soybeans', 'cold tofu', 'egg roll','chilled noodle', 'stir-fried beef and peppers', 'simmered pork', 'boiled chicken and vegetables', 'sashimi bowl', 'sushi bowl','fish-shaped pancake with bean jam', 'shrimp with chill source', 'roast chicken', 'steamed meat dumpling', 'omelet with fried rice','cutlet curry', 'spaghetti meat sauce', 'fried shrimp', 'potato salad', 'green salad', 'macaroni salad', 'Japanese tofu and vegetable chowder','pork miso soup', 'chinese soup','beef bowl', 'kinpira-style sauteed burdock', 'rice ball', 'pizza toast', 'dipping noodles', 'hot dog','french fries', 'mixed rice', 'goya chanpuru', 'others', 'beverage']
    target_count = 3  # アチーブメント達成に必要な回数
    achievements = {}
    for tag_name in tag_names:
        is_achieved = UserImageTag.check_achievement_for_tag(user_id, tag_name, target_count)
        achievements[tag_name] = is_achieved #各タグに対する達成状況true,falseを辞書に格納する
        if is_achieved[0]:  # 達成された場合
            flash(f"{tag_name} のアチーブメント達成！", "success")  # flashメッセージを追加
    
    return render_template('detector/achievements.html', achievements=achievements, user_id=user_id)


def categorize_tag(tag_name):
    if tag_name in [
        'bibimbap', 'ramen noodle', 'beef noodle', 'tensin noodle', 'fried noodle',
        'spicy chili-flavored tofu', 'jiaozi', 'sweet and sour pork', 'fried fish',
        'shrimp with chill source', 'steamed meat dumpling', 'chinese soup',
        'stir-fried beef and peppers'
    ]:
        return "中華"
    elif tag_name in [
        'rice', 'eels on rice', 'chicken-n-egg on rice', 'pork cutlet on rice',
        'sushi', 'chicken rice', 'fried rice', 'tempura bowl', 'udon noodle',
        'tempura udon', 'soba noodle', 'miso soup', 'tempura', 'grilled eggplant',
        'vegetable tempura', 'teriyaki grilled fish', 'grilled salmon', 'salmon meuniere',
        'sashimi', 'grilled pacific saury', 'sukiyaki', 'lightly roasted fish',
        'steamed egg hotchpotch', 'oden', 'omelet', 'ganmodoki', 'grilled salmon',
        'seasoned beef with potatoes', 'hambarg steak', 'dried fish', 'ginger pork saute',
        'yakitori', 'rolled omelet', 'egg sunny-side up', 'fermented soybeans', 'cold tofu',
        'egg roll', 'simmered pork', 'boiled chicken and vegetables', 'sashimi bowl',
        'sushi bowl', 'Japanese tofu and vegetable chowder', 'pork miso soup', 'beef bowl',
        'kinpira-style sauteed burdock', 'rice ball', 'mixed rice', 'goya chanpuru',
        'pizza toast', 'dipping noodles'
    ]:
        return "和食"
    elif tag_name in [
        'pilaf', 'beef curry', 'toast', 'croissant', 'roll bread', 'raisin bread',
        'chip butty', 'hamburger', 'pizza', 'sandwiches', 'gratin', 'potage', 'sausage',
        'stew', 'fried chicken', 'sirloin cutlet', 'beef steak', 'cabbage roll',
        'omelet with fried rice', 'cutlet curry', 'spaghetti meat sauce', 'fried shrimp',
        'potato salad', 'green salad', 'macaroni salad', 'french fries', 'hot dog', 'beverage'
    ]:
        return "洋食"
    else:
        return "その他"
    
#グラフ表示
@dt.route('/category_stats/')
@login_required

def category_stats():
    user_id = current_user.id  # 現在のユーザーIDを取得
    tag_names = ['rice', 'eels on rice', 'pilaf', 'chicken-n-egg on rice', 'pork cutlet on rice', 'beef curry', 'sushi', 'chicken rice', 'fried rice', 'tempura bowl', 'bibimbap', 'toast', 'croissant', 'roll bread', 'raisin bread', 'chip butty', 'hamburger', 'pizza', 'sandwiches', 'udon noodle','tempura udon','soba noodle', 'ramen noodle', 'beef noodle', 'tensin noodle', 'fried noodle', 'spaghetti', 'Japanese-style pancake', 'takoyaki', 'gratin','sauteed vegetables', 'croquette', 'grilled eggplant', 'sauteed spinach', 'vegetable tempura', 'miso soup', 'potage', 'sausage','oden', 'omelet', 'ganmodoki', 'jiaozi', 'stew', 'teriyaki grilled fish', 'fried fish', 'grilled salmon', 'salmon meuniere', 'sashimi','grilled pacific saury ', 'sukiyaki', 'sweet and sour pork', 'lightly roasted fish', 'steamed egg hotchpotch', 'tempura', 'fried chicken','sirloin cutlet', 'nanbanzuke', 'boiled fish','seasoned beef with potatoes', 'hambarg steak', 'beef steak', 'dried fish', 'ginger pork saute','spicy chili-flavored tofu', 'yakitori', 'cabbage roll', 'rolled omelet', 'egg sunny-side up', 'fermented soybeans', 'cold tofu', 'egg roll','chilled noodle', 'stir-fried beef and peppers', 'simmered pork', 'boiled chicken and vegetables', 'sashimi bowl', 'sushi bowl','fish-shaped pancake with bean jam', 'shrimp with chill source', 'roast chicken', 'steamed meat dumpling', 'omelet with fried rice','cutlet curry', 'spaghetti meat sauce', 'fried shrimp', 'potato salad', 'green salad', 'macaroni salad', 'Japanese tofu and vegetable chowder','pork miso soup', 'chinese soup','beef bowl', 'kinpira-style sauteed burdock', 'rice ball', 'pizza toast', 'dipping noodles', 'hot dog','french fries', 'mixed rice', 'goya chanpuru', 'others', 'beverage']
    all_count = {}
    tyuka_total = 0
    yosyoku_total = 0
    wasyoku_total = 0
    other_total = 0
    for tag_name in tag_names:
        is_count = UserImageTag.count_tag_for_user(user_id, tag_name)
        jyanru = categorize_tag(tag_name)
        if jyanru == "中華":
            tyuka_total += is_count
        elif jyanru == "洋食":
            yosyoku_total += is_count
        elif jyanru == "和食":
            wasyoku_total += is_count
        else:
            other_total += is_count

        all_count[tag_name] = is_count
    
    # 日付ごとに関連するタグを取得し、カロリーを計算
    date_calories = {}
    tag_query = (
        db.session.query(UserImageTag.created_at, UserImageTag.tag_name)
        .join(UserImage)
        .filter(UserImage.user_id == user_id)
        .all()
    )
    for created_at, tag_name in tag_query:
        date_key = created_at.strftime('%Y-%m-%d') if created_at else "1970-01-01"
        tag_calories = tag_info.get(tag_name, {}).get('calories', 0)
        if date_key in date_calories:
            date_calories[date_key] += tag_calories
        else:
            date_calories[date_key] = tag_calories

    # 日付順にソートしてリスト化
    dates = sorted(date_calories.keys())
    calories_list = [date_calories[date] for date in dates]

    return render_template('detector/category_stats.html', 
                           all_count=all_count, 
                           user_id=user_id, 
                           tyuka_total=tyuka_total, 
                           yosyoku_total=yosyoku_total,
                           wasyoku_total=wasyoku_total,
                           other_total=other_total,
                           dates=dates,
                           calories_list=calories_list)

from sqlalchemy.sql import func

def get_daily_tag_counts(user_id):
    # 日付ごとのタグ数を集計
    daily_tag_counts = (
        db.session.query(
            func.date(UserImage.detected_at).label("date"),  # 日付
            func.count(UserImageTag.id).label("tag_count")  # タグ数
        )
        .join(UserImageTag, UserImage.id == UserImageTag.user_image_id)
        .filter(UserImage.user_id == user_id)  # 現在のユーザーに限定
        .group_by(func.date(UserImage.detected_at))  # 日付ごとにグループ化
        .order_by(func.date(UserImage.detected_at))  # 日付順に並べる
        .all()
    )
    return daily_tag_counts
def daily_tags():
    user_id = current_user.id  # 現在のユーザーID
    daily_tag_counts = get_daily_tag_counts(user_id)
    
    # グラフ用データを整形
    dates = [entry.date.strftime("%Y-%m-%d") for entry in daily_tag_counts]
    tag_counts = [entry.tag_count for entry in daily_tag_counts]
    
    return render_template(
        'detector/category_stats.html',
        dates=dates,
        tag_counts=tag_counts
    )


@dt.route("/add_tag", methods=["POST"])
def add_tag():
    tag_name = request.form.get("tag_name")
    image_id = request.form.get("image_id")

    # カテゴリを自動判定して設定
    category = categorize_tag(tag_name)

    new_tag = UserImageTag(user_image_id=image_id, tag_name=tag_name, category=category)
    db.session.add(new_tag)
    db.session.commit()

    flash("タグが追加されました！", "success")
    return redirect(url_for("image_detail", image_id=image_id))


from datetime import datetime, timedelta
from flask import render_template
from flask_login import login_required, current_user

@dt.route('/daily_missions/')
@login_required

def daily_missions():
    user_id = 3
    today = datetime.now().date()  # 今日の日付を取得

    # 今日投稿された画像を取得
    user_images = db.session.query(UserImage).join(User).filter(
        UserImage.user_id == user_id,
        UserImage.detected_at >= today,
        UserImage.detected_at < today + timedelta(days=1)
    ).all()

    # 時間帯ごとのミッション進捗
    mission_status = {
        '朝食': False,
        '昼食': False,
        '夕食': False
    }

    # デバッグメッセージ: 取得したユーザーの画像情報を確認
    current_app.logger.debug(f"ユーザーID: {user_id}")
    current_app.logger.debug(f"今日投稿された画像数: {len(user_images)}")

    # 画像ごとに時間帯を確認してミッションステータスを更新
    for image in user_images:
        hour = image.detected_at.hour
        current_app.logger.debug(f"画像の投稿時間: {image.detected_at} ({hour}時)")

        if 5 <= hour < 10:
            mission_status['朝食'] = True
        elif 10 <= hour < 15:
            mission_status['昼食'] = True
        elif 15 <= hour < 22:
            mission_status['夕食'] = True

    # 朝食ミッションが達成されているか確認
    if mission_status['朝食']:
        current_app.logger.debug("朝食ミッションが達成されました")
    else:
        current_app.logger.debug("朝食ミッションは未達成")

    # 昼食ミッションが達成されているか確認
    if mission_status['昼食']:
        current_app.logger.debug("昼食ミッションが達成されました")
    else:
        current_app.logger.debug("昼食ミッションは未達成")

    # 夕食ミッションが達成されているか確認
    if mission_status['夕食']:
        current_app.logger.debug("夕食ミッションが達成されました")
    else:
        current_app.logger.debug("夕食ミッションは未達成")

    # ミッションの進捗をテンプレートに渡す
    return render_template('detector/index.html', 
                           todaymeal = user_images,
                           mission_status=mission_status)

