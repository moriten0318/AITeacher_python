import sys
import io
import json
import os
import openai
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import gspread
import socket
import time

from llama_index import (
    download_loader
)


#APIキー取得して渡す
load_dotenv()
api_key = os.environ['OPENAI_API_KEY']
print(api_key)
openai.api_key=api_key

#Googleスプレッドシート認証用
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
json_pass="gspread-400109-00716d87edde.json"
#認証用のJSONファイルのパスを貼る(\は2個に変えること！)
#ここ変更しないと別環境では動かないので注意！
credentials = Credentials.from_service_account_file(
    (os.path.dirname(__file__)).replace("C","c")+"\\"+json_pass,
    scopes=scopes
)
gc = gspread.authorize(credentials)#GoogleAPIにログイン
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1g4g0UNh74WJmemhGR3ftCQUWyt2_GbmYonw6CHo0XHo/edit#gid=0"

#UDP通信用設定
HOST = '127.0.0.1'
PORT = 50007
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

lastnum = 0
ID=0
current_list = []

setting ="あなたの名前=ハル\
    あなたの背景設定=バーチャル世界に存在するAI教師\
    日本語で答えてください。質問に関係ないことは、話さないでください。\
    出力は必ず簡潔に答えてください。それが不可能な場合でもできるだけ、少なくなるようにして下さい。"

# loader = download_loader("CJKPDFReader")#PDFローダーを準備

# filelist=["index_test","クリスパー・キャス","ダークマター","水筒","星が光って見えるのはなぜだろう"]
information=""

# 特定のフォルダ内からキーワードを含むJSONファイルを開く
folder_path = "//lessondata"
keyword = 'honji'

#指定フォルダからJSONファイルを取得
def open_json(folder_path, keyword):
    # フォルダ内のすべてのファイルを取得
    file_list = os.listdir(folder_path)

    # JSONファイルを検索し、指定のキーワードを含むファイルを見つける
    for filename in file_list:
        if filename.endswith('.json') and keyword in filename:
            file_path = os.path.join(folder_path, filename)
            with open(file_path, encoding='utf-8') as file:
                return json.load(file)
    
    # 指定の条件を満たすJSONファイルが見つからない場合、Noneを返す
    return None


#シートの初期化
def initialize_sheet():
    workbook = gc.open_by_url(spreadsheet_url)
    sheet1 = workbook.worksheet("質問シート")
    sheet2 = workbook.worksheet("保存シート")
    # シート1のデータを読み取る
    data_sheet1 = sheet1.get_all_values()
    # シート2の最後の行を特定
    last_row = len(sheet2.get_all_values()) + 1
    # シート2にバックアップ
    for row in data_sheet1:
        sheet2.insert_row(row, last_row)
        last_row += 1
    # シート1の内容を消去
    sheet1.clear()


#スプレッドシートを取得するための関数
def get_sheet():        
    spreadsheet = gc.open_by_url(spreadsheet_url).sheet1
    import_value = spreadsheet.col_values(2)#B行の要素を取得
    print(import_value)
    return import_value
    #spreadsheet.acell('B'+cell_number).value

#UDP通信周りの関数
def UDP(content):
    client.sendto(content.encode('utf-8'),(HOST,PORT))


def send_message_to_unity(message, message_id, is_response):
    # 送信するデータをJSON形式に変換
    json_data = json.dumps({
        "id": message_id,
        "content": message,
        "isResponse": is_response
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    # データを送信
    sock.sendto(json_data.encode("utf-8"), (HOST,PORT))
    sock.close()

#返答生成
def generate_answer(prompt, conversation_history,message_id):
    # プロンプトを会話履歴に追加
    conversation_history.append({"role": "user", "content": prompt})
    # GPT-4モデルを使用する場合
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )
    message = ""
    for choice in response.choices:
        message += choice.message['content']

    # 応答文を会話履歴に追加
    conversation_history.append({"role": "assistant", "content": message})
    # Unityにメッセージを送信
    send_message_to_unity(message, message_id, True)#レスポンスフラグ有でUnityに送信
    return message



###メインループ！！！###
if __name__ == "__main__":
    # 会話履歴を格納するためのリストを初期化
    conversation_history = []
    #設定を追加
    conversation_history.append({"role": "system", "content": setting})
    # 実行ファイルのディレクトリを取得
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # lessondataフォルダのパスを作成
    lessondata_folder = os.path.join(current_directory, 'lessondata')
    #授業の発話を記憶として追加する
    json_data = open_json(lessondata_folder, keyword)
    # "教師の発話"の値を取り出して一つの文章に結合
    information = "".join(item["教師の発話"] for item in json_data)
    information=information+"上記はあなたの記憶です。質問を受け取ったら、上記の内容を踏まえながら解答を生成してください。"
    conversation_history.append({"role": "system", "content": information})

    initialize_sheet()

    #mainループ
    while True:
        
        new_list = get_sheet()    
        if new_list==current_list:
            print("更新はありません")
            time.sleep(3.0)
            continue
        else:
        #スプレッドシートに更新があったときの処理
            # for i in range(lastnum,len(new_list)):
            #     print(new_list[i])
            #     ans=generate_text(new_list[i], conversation_history)
            #     UDP(new_list[i]+"@"+str(ans))

            for i in range(lastnum,len(new_list)):
                # メッセージが「クイズに解答:」で始まるかどうかをチェック
                if new_list[i].startswith('クイズに解答:'):
                    # 数字部分を取得
                    quiz_answer = new_list[i].split(':')[1]

                    # ここで数字に基づいて特定の処理を行う
                    if quiz_answer == '1':
                        # 数字が1の場合の処理
                        # 例: 特定の回答を送る、特定の処理を行う、など
                        #print(1)
                        pass
                    elif quiz_answer == '2':
                        # 数字が2の場合の処理
                        #print(2)
                        pass
                    elif quiz_answer == '3':
                        # 数字が3の場合の処理
                        #print(3)
                        pass
                else:                
                    print(new_list[i])
                    send_message_to_unity(new_list[i],ID, False)
                    generate_answer(new_list[i], conversation_history,ID)
                    ID+=1
            current_list = new_list
            lastnum = len(current_list)
            time.sleep(1.0)


# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
