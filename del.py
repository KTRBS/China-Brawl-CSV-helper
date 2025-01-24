import pandas as pd
import os

# ファイル名
ktr_file = 'ktr.csv'

# ファイルの存在確認
if not os.path.exists(ktr_file):
    print(f"エラー: ファイル {ktr_file} が見つかりません。")
else:
    try:
        # CSVファイルを読み込む
        ktr_data = pd.read_csv(ktr_file)

        # 重複行を確認
        duplicates = ktr_data[ktr_data.duplicated()]
        if not duplicates.empty:
            print("以下の重複行が見つかりました:")
            print(duplicates)

            # 重複を削除
            ktr_data_cleaned = ktr_data.drop_duplicates()

            # ファイルに上書き保存
            ktr_data_cleaned.to_csv(ktr_file, index=False)
            print(f"{len(duplicates)} 行の重複を削除し、{ktr_file} を更新しました。")
        else:
            print("重複行は見つかりませんでした。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")