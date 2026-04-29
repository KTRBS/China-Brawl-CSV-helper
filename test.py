import os
import logging
import pandas as pd
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

# ロギング
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_BOT_TOKEN_HERE"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 会話の状態
WAITING_KTR, WAITING_TEXTS, WAITING_CN = range(3)

def get_decoded_path(original_path):
    """
    decode_file実行後、別名ファイルが生成されていればそのパスを、
    無ければ元のパス（上書き想定）を返す補助関数。
    """
    decoded_path = original_path.replace(".csv", ".decoded.csv")
    return decoded_path if os.path.exists(decoded_path) else original_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("1. ベースとなる **ktr.csv** を送信してください。")
    return WAITING_KTR

async def process_ktr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_ktr.csv")
    file = await update.message.document.get_file()
    await file.download_to_drive(path)
    
    try:
        decode_file(path) # デコード実行
        context.user_data["ktr_path"] = get_decoded_path(path)
        await update.message.reply_text("ktr.csvをデコードしました。\n\n2. 次に **texts.csv** を送信してください（これもデコードします）。")
        return WAITING_TEXTS
    except Exception as e:
        await update.message.reply_text(f"デコードエラー: {e}")
        return WAITING_KTR

async def process_texts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_texts.csv")
    file = await update.message.document.get_file()
    await file.download_to_drive(path)
    
    try:
        decode_file(path) # デコード実行
        context.user_data["texts_path"] = get_decoded_path(path)
        await update.message.reply_text("texts.csvをデコードしました。\n\n3. 最後に **cn.csv** を送信してください。")
        return WAITING_CN
    except Exception as e:
        await update.message.reply_text(f"デコードエラー: {e}")
        return WAITING_TEXTS

async def process_cn_and_merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_cn.csv")
    file = await update.message.document.get_file()
    await file.download_to_drive(path)

    try:
        decode_file(path) # デコード実行
        cn_path = get_decoded_path(path)
        ktr_path = context.user_data["ktr_path"]
        texts_path = context.user_data["texts_path"]

        await update.message.reply_text("全ファイルのデコード完了。TIDを照合してマージを開始します...")

        # 2行目(string,string)をスキップしてデータとして読み込む
        def load_csv(p): return pd.read_csv(p, skiprows=[1])

        df_ktr = load_csv(ktr_path)
        df_texts = load_csv(texts_path)
        df_cn = load_csv(cn_path)

        # 1. texts.csv から ktr に存在しない TID を追加
        new_texts = df_texts[~df_texts['TID'].isin(df_ktr['TID'])]
        df_merged = pd.concat([df_ktr, new_texts], ignore_index=True)

        # 2. cn.csv から merged(ktr+texts) に存在しない TID を追加
        new_cn = df_cn[~df_cn['TID'].isin(df_merged['TID'])]
        df_final = pd.concat([df_merged, new_cn], ignore_index=True)

        # 出力ファイルの作成（ヘッダーと型定義を復元）
        result_csv = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_result.csv")
        with open(result_csv, 'w', encoding='utf-8') as f:
            f.write("TID,CN\nstring,string\n")
            df_final.to_csv(f, index=False, header=False, lineterminator='\n')

        # 結果をエンコード
        encode_file(result_csv)
        encoded_result = result_csv.replace(".csv", ".encoded.csv")
        if not os.path.exists(encoded_result): encoded_result = result_csv

        # ユーザーに送信
        with open(encoded_result, "rb") as f:
            await update.message.reply_document(
                document=f, 
                filename="merged_result.csv",
                caption="すべてのファイルをデコード・マージし、最後に再度エンコードしました。"
            )

        # 一時ファイルの削除（任意）
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"処理中にエラーが発生しました: {e}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("プロセスを中断しました。")
    return ConversationHandler.END

def main():
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
    application.run_polling()

if __name__ == "__main__":
    main()
