import pandas as pd
import os

ktr_file = 'ktr.csv'
texts_file = 'texts.csv'

if not os.path.exists(ktr_file):
    print(f"{ktr_file} doesnt exist.")
    exit()

if not os.path.exists(texts_file):
    print(f"{texts_file} doesnt exist.")
    exit()

ktr_data = pd.read_csv(ktr_file)
texts_data = pd.read_csv(texts_file)

new_data = texts_data[~texts_data.isin(ktr_data.to_dict(orient='list')).all(axis=1)]

if not new_data.empty:
    new_data.to_csv(ktr_file, mode='a', header=False, index=False)
    print(f"added {len(new_data)} lines to{ktr_file} ")
else:
    print("nothinfg was added")
