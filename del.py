import pandas as pd
import os

ktr_file = 'ktr.csv'

if not os.path.exists(ktr_file):
    print(f"error: {ktr_file} doesnt exist")
else:
    try:
        ktr_data = pd.read_csv(ktr_file)
        
        duplicates = ktr_data[ktr_data.duplicated()]
        if not duplicates.empty:
            print("Duplicates found:")
            print(duplicates)

            ktr_data_cleaned = ktr_data.drop_duplicates()

            ktr_data_cleaned.to_csv(ktr_file, index=False)
            print(f"Removed {len(duplicates)} duplicates and updated {ktr_file} .")
        else:
            print("No duplicates were foind")
    except Exception as e:
        print(f"error: {e}")
