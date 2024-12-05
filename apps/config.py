from pathlib import Path

basedir = Path(__file__).parent.parent

#BaseConfigクラスを作成する
class BaseConfig:
    SECRET_KEY = "2AZSMss3p5QPbcY2hBsJ"
    WTF_CSRF_SECRET_KEY = "AuwzyszU5sugKN7KZs6f"
    #画像アップロード先にapps/imagesを指定する
    UPLOAD_FOLDER=str(Path(basedir, "apps", "images"))

    #物体検知に利用するラベル
    LABELS =  ['rice', 'eels on rice', 'pilaf', 'chicken-n-egg on rice', 'pork cutlet on rice', 'beef curry', 'sushi', 'chicken rice', 'fried rice', 'tempura bowl', 'bibimbap', 'toast', 'croissant', 'roll bread', 'raisin bread', 'chip butty', 'hamburger', 'pizza', 'sandwiches', 'udon noodle','tempura udon','soba noodle', 'ramen noodle', 'beef noodle', 'tensin noodle', 'fried noodle', 'spaghetti', 'Japanese-style pancake', 'takoyaki', 'gratin','sauteed vegetables', 'croquette', 'grilled eggplant', 'sauteed spinach', 'vegetable tempura', 'miso soup', 'potage', 'sausage','oden', 'omelet', 'ganmodoki', 'jiaozi', 'stew', 'teriyaki grilled fish', 'fried fish', 'grilled salmon', 'salmon meuniere', 'sashimi',
        'grilled pacific saury ', 'sukiyaki', 'sweet and sour pork', 'lightly roasted fish', 'steamed egg hotchpotch', 'tempura', 'fried chicken','sirloin cutlet', 'nanbanzuke', 'boiled fish','seasoned beef with potatoes', 'hambarg steak', 'beef steak', 'dried fish', 'ginger pork saute','spicy chili-flavored tofu', 'yakitori', 'cabbage roll', 'rolled omelet', 'egg sunny-side up', 'fermented soybeans', 'cold tofu', 'egg roll','chilled noodle', 'stir-fried beef and peppers', 'simmered pork', 'boiled chicken and vegetables', 'sashimi bowl', 'sushi bowl','fish-shaped pancake with bean jam', 'shrimp with chill source', 'roast chicken', 'steamed meat dumpling', 'omelet with fried rice',
        'cutlet curry', 'spaghetti meat sauce', 'fried shrimp', 'potato salad', 'green salad', 'macaroni salad', 'Japanese tofu and vegetable chowder','pork miso soup', 'chinese soup','beef bowl', 'kinpira-style sauteed burdock', 'rice ball', 'pizza toast', 'dipping noodles', 'hot dog','french fries', 'mixed rice', 'goya chanpuru', 'others', 'beverage']

#BaseConfigクラスを継承してLocalConfigクラスを作成する
class LocalConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'local.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SQLALCHEMY_ECHO=True

#BaseConfigクラスを継承してTestingConfigクラスを作成する
class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'testing.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SQLALCHEMY_ECHO=True

class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'production.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 例えば、本番環境ではSQLのログ出力を無効にする


#config辞書にマッピングする
config = {"testing":TestingConfig,
          "local":LocalConfig,
          "production": ProductionConfig,}
