import os
import logging
import pandas as pd
import csv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from lib_csv import encode_file, decode_file

# ロギング設定
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_BOT_TOKEN_HERE"

# Pydroid3でも安定するように絶対パスを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_actual_path(original_path, suffix=".decoded.csv"):
    """
    デコード後のファイルパスを確定させる。
    1. original.decoded.csv
    2. original.csv.decoded.csv (lib_csvの仕様に合わせる)
    3. original.csv (上書きの場合)
    を順番に探し、最初に見つかった「中身のあるファイル」を返します。
    """
    targets = [
        original_path.replace(".csv", suffix),
        original_path + suffix,
        original_path
    ]
    for t in targets:
        if os.path.exists(t) and os.path.getsize(t) > 0:
            logger.info(f"Found valid file: {t}")
            return t
    return None

def load_custom_csv(p):
    """ダブルクォーテーションを考慮し、中身の空チェックを行って読み込む"""
    if p is None or not os.path.exists(p):
        raise Exception("ファイルが見つかりません。デコードに失敗した可能性があります。")
    if os.path.getsize(p) == 0:
        raise Exception(f"ファイル {os.path.basename(p)} が空(0バイト)です。")
    
    return pd.read_csv(
        p, 
        skiprows=[1], 
        quotechar='"', 
        skipinitialspace=True,
        engine='python',
        encoding='utf-8'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("ktr, texts, cn の3ファイルを送信してください。")

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    f_name = doc.file_name.lower()
    user_id = update.effective_user.id
    
    f_type = None
    if "ktr" in f_name: f_type = "ktr"
    elif "texts" in f_name: f_type = "texts"
    elif "cn" in f_name: f_type = "cn"
    
    if not f_type: return

    # 保存先を絶対パスで指定
    save_path = os.path.join(UPLOAD_DIR, f"{user_id}_{f_type}.csv")
    file = await doc.get_file()
    await file.download_to_drive(save_path)
    
    if "files" not in context.user_data: context.user_data["files"] = {}
    context.user_data["files"][f_type] = save_path
    
    await update.message.reply_text(f"受信: {f_type} ({len(context.user_data['files'])}/3)")

    if len(context.user_data["files"]) == 3:
        await proceed_merge(update, context)

async def proceed_merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    files = context.user_data["files"]

    try:
        # 1. 全ファイルをデコードし、パスを確定
        decoded_paths = {}
        for ftype, path in files.items():
            decode_file(path)
            actual = get_actual_path(path, ".decoded.csv")
            if not actual:
                raise Exception(f"{ftype}のデコード後のファイルが見つからないか、空です。")
            decoded_paths[ftype] = actual

        # 2. 読み込み
        df_ktr = load_custom_csv(decoded_paths["ktr"])
        df_texts = load_custom_csv(decoded_paths["texts"])
        df_cn = load_custom_csv(decoded_paths["cn"])

        # 3. マージ
        new_texts = df_texts[~df_texts['TID'].isin(df_ktr['TID'])]
        df_merged = pd.concat([df_ktr, new_texts], ignore_index=True)
        new_cn = df_cn[~df_cn['TID'].isin(df_merged['TID'])]
        df_final = pd.concat([df_merged, new_cn], ignore_index=True)

        # 4. 保存
        res_csv = os.path.join(UPLOAD_DIR, f"{user_id}_final.csv")
        with open(res_csv, 'w', encoding='utf-8', newline='') as f:
            f.write('"TID","CN"\n"string","string"\n')
            df_final.to_csv(f, index=False, header=False, quoting=csv.QUOTE_ALL, lineterminator='\n')

        # 5. エンコード
        encode_file(res_csv)
        final_file = get_actual_path(res_csv, ".encoded.csv")

        with open(final_file, "rb") as f:
            await update.message.reply_document(f, filename="merged_result.csv")

        context.user_data.clear()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"エラー発生:\n{e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.run_polling()

if __name__ == "__main__":
    main()
