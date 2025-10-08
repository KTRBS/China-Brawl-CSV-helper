import csv
import os

texts_path = "texts.csv"
cn_path = "cn.csv"
ktr_path = "ktr.csv"

seen_lines = set()
all_lines = []

# read ktr.csv
if os.path.exists(ktr_path):
    with open(ktr_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            seen_lines.add(tuple(line))

print("importing texts.csv")
if os.path.exists(texts_path):
    with open(texts_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            tuple_line = tuple(line)
            if tuple_line not in seen_lines:
                seen_lines.add(tuple_line)
                all_lines.append(tuple_line)
print("texts.csv imported")

print("importing cn.csv")
if os.path.exists(cn_path):
    with open(cn_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            tuple_line = tuple(line)
            if tuple_line not in seen_lines:
                seen_lines.add(tuple_line)
                all_lines.append(tuple_line)
print("done importing")

# remove existing lines
print("removing existing lines...")
final_lines = []
seen = set()
removed_count = 0
for line in all_lines:
    if line not in seen:
        final_lines.append(line)
        seen.add(line)
    else:
        removed_count += 1

print(f"removed {removed_count} duplicate lines")

# write
with open(ktr_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(final_lines)

print("done ✅")
