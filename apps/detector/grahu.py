import pandas as pd
import matplotlib.pyplot as plt

# カテゴリごとの料理リスト
categories = {
    '中華': [
        'fried rice', 'sweet and sour pork', 'jiaozi', 'chow mein',
        'beef noodle', 'tensin noodle', 'spicy chili-flavored tofu', 
        'dumplings', 'wontons', 'kung pao chicken'
    ],
    '和食': [
        'sushi', 'ramen noodle', 'tempura', 'miso soup', 
        'udon noodle', 'soba noodle', 'takoyaki', 'gratin',
        'beef bowl', 'chirashi sushi'
    ],
    '洋食': [
        'hamburger', 'pizza', 'spaghetti', 'croissant', 
        'toast', 'roll bread', 'french fries', 'sandwiches',
        'gratin', 'beef steak'
    ],
    'その他': [
        'beverage', 'snack', 'salad', 'omelet', 'chilled noodle'
    ]
}

# 料理とそのカテゴリをリストに変換
data = []
for category, dishes in categories.items():
    for dish in dishes:
        data.append({'Category': category, 'Dish': dish})

# データフレームの作成
df = pd.DataFrame(data)

# 各カテゴリの料理名を表示
for category, dishes in categories.items():
    print(f"{category}の料理: {', '.join(dishes)}")

# カテゴリごとの料理数をカウント
category_counts = df['Category'].value_counts()

# グラフの作成
plt.figure(figsize=(10, 6))
category_counts.plot(kind='bar', color='skyblue')
plt.title('Category Counts of Dishes')
plt.xlabel('Category')
plt.ylabel('Number of Dishes')  # Y軸ラベルを設定
plt.xticks(rotation=45)
plt.grid(axis='y')

plt.tight_layout()  # レイアウトを調整
plt.show()  # グラフを表示
