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
    ConversationHandler,
)
# lib_csv.py（decode_file, encode_fileを含む）が同ディレクトリにある前提
from lib_csv import encode_file, decode_file

# ロギング設定
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 設定項目 ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 会話の状態定義
WAITING_KTR, WAITING_TEXTS, WAITING_CN = range(3)

def get_processed_path(original_path, suffix=".decoded.csv"):
    """デコードやエンコード後にファイル名が変わる場合に対応する補助関数"""
    new_path = original_path.replace(".csv", suffix)
    return new_path if os.path.exists(new_path) else original_path

def load_custom_csv(p):
    """
    1行目がヘッダー、2行目が型定義(string,string)のCSVを読み込む。
    ダブルクォーテーションの囲いを考慮する。
    """
    return pd.read_csv(
        p, 
        skiprows=[1],       # 2行目の "string","string" をスキップ
        quotechar='"',      # ダブルクォーテーションを引用符として扱う
        skipinitialspace=True,
        engine='python'     # 柔軟な解析のためpythonエンジンを使用
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "CSVインポートプロセスを開始します。\n\n"
        "1. まずはベースとなる **ktr.csv** を送信してください。"
    )
    return WAITING_KTR

async def process_ktr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_ktr.csv")
    file = await update.message.document.get_file()
    await file.download_to_drive(path)
    
    try:
        decode_file(path)
        context.user_data["ktr_path"] = get_processed_path(path, ".decoded.csv")
        await update.message.reply_text("ktr.csvをデコードしました。\n\n2. 次に **texts.csv** を送信してください。")
        return WAITING_TEXTS
    except Exception as e:
        await update.message.reply_text(f"ktrの処理中にエラー: {e}")
        return WAITING_KTR

async def process_texts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_texts.csv")
    file = await update.message.document.get_file()
    await file.download_to_drive(path)
    
    try:
        decode_file(path)
        context.user_data["texts_path"] = get_processed_path(path, ".decoded.csv")
        await update.message.reply_text("texts.csvをデコードしました。\n\n3. 最後に **cn.csv** を送信してください。")
        return WAITING_CN
    except Exception as e:
        await update.message.reply_text(f"textsの処理中にエラー: {e}")
        return WAITING_TEXTS

async def process_cn_and_merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_cn.csv")
    file = await update.message.document.get_file()
    await file.download_to_drive(path)

    try:
        decode_file(path)
        cn_path = get_processed_path(path, ".decoded.csv")
        ktr_path = context.user_data["ktr_path"]
        texts_path = context.user_data["texts_path"]

        await update.message.reply_text("マージ処理を開始します...")

        # データの読み込み
        df_ktr = load_custom_csv(ktr_path)
        df_texts = load_custom_csv(texts_path)
        df_cn = load_custom_csv(cn_path)

        # マージロジック: TIDがktrに存在しないものをtextsから追加
        new_texts = df_texts[~df_texts['TID'].isin(df_ktr['TID'])]
        df_merged = pd.concat([df_ktr, new_texts], ignore_index=True)

        # マージロジック: TIDがここまでの結果に存在しないものをcnから追加
        new_cn = df_cn[~df_cn['TID'].isin(df_merged['TID'])]
        df_final = pd.concat([df_merged, new_cn], ignore_index=True)

        # 結果の保存（ヘッダーと型定義を復元し、全てをダブルクォーテーションで囲む）
        result_csv = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_final_result.csv")
        with open(result_csv, 'w', encoding='utf-8', newline='') as f:
            f.write('"TID","CN"\n"string","string"\n')
            df_final.to_csv(
                f, 
                index=False, 
                header=False, 
                quoting=csv.QUOTE_ALL, # 全ての項目を "" で囲む
                lineterminator='\n'
            )

        # エンコード処理
        encode_file(result_csv)
        final_file = get_processed_path(result_csv, ".encoded.csv")

        # ファイル送信
        with open(final_file, "rb") as f:
            await update.message.reply_document(
                document=f, 
                filename="merged_result.csv",
                caption="全ファイルのデコード、TID照合マージ、再エンコードが完了しました。"
            )

        # 終了
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Merge error: {e}")
        await update.message.reply_text(f"処理中にエラーが発生しました:\n{e}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("中断しました。/start でやり直せます。")
    return ConversationHandler.END

def main():
    """Botの起動"""
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_KTR: [MessageHandler(filters.Document.ALL, process_ktr)],
            WAITING_TEXTS: [MessageHandler(filters.Document.ALL, process_texts)],
            WAITING_CN: [MessageHandler(filters.Document.ALL, process_cn_and_merge)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
