import os
import logging
import pandas as pd
import csv
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
# lib_csv.py（decode_file, encode_fileを含む）が同ディレクトリにある前提
from lib_csv import encode_file, decode_file

# ロギング設定
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 設定項目 ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_processed_path(original_path, suffix=".decoded.csv"):
    """デコードやエンコード後にファイル名が変わる場合に対応"""
    new_path = original_path.replace(".csv", suffix)
    return new_path if os.path.exists(new_path) else original_path

def load_custom_csv(p):
    """ダブルクォーテーションの囲いを考慮してCSVを読み込む"""
    return pd.read_csv(
        p, 
        skiprows=[1], 
        quotechar='"', 
        skipinitialspace=True,
        engine='python'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "CSV一括インポートボットです。\n"
        "**ktr.csv**, **texts.csv**, **cn.csv** の3ファイルを送信してください。\n"
        "（一度に送っても、バラバラに送っても大丈夫です）"
    )

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name.lower()
    user_id = update.effective_user.id
    
    # ファイルの分類
    file_type = None
    if "ktr" in file_name:
        file_type = "ktr"
    elif "texts" in file_name:
        file_type = "texts"
    elif "cn" in file_name:
        file_type = "cn"
    
    if not file_type:
        await update.message.reply_text(f"無視されました: {doc.file_name}\n(ファイル名に ktr, texts, cn のいずれかを含めてください)")
        return

    # ダウンロード
    path = os.path.join(UPLOAD_DIR, f"{user_id}_{file_type}.csv")
    file = await doc.get_file()
    await file.download_to_drive(path)
    
    # ユーザーデータに保存
    if "files" not in context.user_data:
        context.user_data["files"] = {}
    context.user_data["files"][file_type] = path
    
    current_files = list(context.user_data["files"].keys())
    await update.message.reply_text(f"受信完了: {file_type} ({len(current_files)}/3 揃いました)")

    # 3つ揃ったら処理開始
    if len(current_files) == 3:
        await proceed_merge(update, context)

async def proceed_merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    files = context.user_data["files"]
    await update.message.reply_text("3つのファイルが揃いました。全ファイルをデコードしてマージを開始します...")

    try:
        # 1. 全ファイルをデコード
        decoded_paths = {}
        for ftype, path in files.items():
            decode_file(path)
            decoded_paths[ftype] = get_processed_path(path, ".decoded.csv")

        # 2. データの読み込み
        df_ktr = load_custom_csv(decoded_paths["ktr"])
        df_texts = load_custom_csv(decoded_paths["texts"])
        df_cn = load_custom_csv(decoded_paths["cn"])

        # 3. マージロジック (TID照合)
        # textsからktrにないものを追加
        new_texts = df_texts[~df_texts['TID'].isin(df_ktr['TID'])]
        df_merged = pd.concat([df_ktr, new_texts], ignore_index=True)

        # cnからこれまでにないものを追加
        new_cn = df_cn[~df_cn['TID'].isin(df_merged['TID'])]
        df_final = pd.concat([df_merged, new_cn], ignore_index=True)

        # 4. 結果の保存 (囲いあり)
        result_csv = os.path.join(UPLOAD_DIR, f"{user_id}_final_result.csv")
        with open(result_csv, 'w', encoding='utf-8', newline='') as f:
            f.write('"TID","CN"\n"string","string"\n')
            df_final.to_csv(f, index=False, header=False, quoting=csv.QUOTE_ALL, lineterminator='\n')

        # 5. エンコード処理
        encode_file(result_csv)
        final_file = get_processed_path(result_csv, ".encoded.csv")

        # 6. 送信
        with open(final_file, "rb") as f:
            await update.message.reply_document(
                document=f, 
                filename="merged_result.csv",
                caption="一括処理が完了しました。"
            )

        # データの消去（次の処理のため）
        context.user_data.clear()

    except Exception as e:
        logger.error(f"Merge error: {e}")
        await update.message.reply_text(f"エラーが発生しました:\n{e}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    # 全てのドキュメント（ファイル）を同じ関数で受ける
    application.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
