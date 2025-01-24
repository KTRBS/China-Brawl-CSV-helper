import pandas as pd
import os

# ファイル名
ktr_file = 'ktr.csv'
texts_file = 'texts.csv'

# フォルダ内にファイルが存在するか確認
if not os.path.exists(ktr_file):
    print(f"{ktr_file} が存在しません。")
    exit()

if not os.path.exists(texts_file):
    print(f"{texts_file} が存在しません。")
    exit()

# CSVファイルを読み込む
ktr_data = pd.read_csv(ktr_file)
texts_data = pd.read_csv(texts_file)

# ktr.csvに存在しない行を取得
new_data = texts_data[~texts_data.isin(ktr_data.to_dict(orient='list')).all(axis=1)]

# 新しいデータがある場合、ktr.csvに追加
if not new_data.empty:
    new_data.to_csv(ktr_file, mode='a', header=False, index=False)
    print(f"{len(new_data)} 行を {ktr_file} に追加しました。")
else:
    print("追加する行はありませんでした。")