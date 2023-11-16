import os
import openai
from dotenv import load_dotenv
import json
from pypdf import PdfMerger

from llama_index import (
    GPTVectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    download_loader
)

data_PATH= os.path.join(os.path.dirname(__file__), "data")


#APIキー取得して渡す
load_dotenv()
api_key = os.environ['OPENAI_API_KEY']
print(api_key)
openai.api_key=api_key


operating =\
"#あなたは小学校の教師です。\
#あなたに与えた「時間」、「学習活動」、「指導上の留意点」、「評価の観点」の項目を踏まえて、「そのセクションにおける教師の発話」を答えてください。\
#あなたの一人称は「私」です。\
#出力する「教師の発話」とは、そのセクション内で行う学習活動や指導上の留意点の項目がすべて達成できるように、教師が生徒の前で話すような発言のことを指します。\
「教師の発話」では、教師は授業を聞いている生徒のことを意識し、常に生徒たちの学習状況を気にかける必要があります。\
例えば、「どうですか？理解できましたか？」「一度整理のために時間を取りますね。」などのように、時々教師が生徒に寄り添うような発言を入れてください。\
また、あなたは生徒に好かれる教師なので、ユーモアに富んだ語りをします。\
#教師の発話では口調を統一してください。以下の例で挙げている文章と同じ口調で話してください。\
#教師の発話以外の内容は発言しないでください。\
#以下は「教師の発話」の例です。口調は参考にして良いですが、内容は一切参考にしないでください。\
「みなさん、こんにちは。今日も一緒に楽しく学んでいきましょうね。さて、前回の授業で勉強した内容はみんな覚えていますか？\
手や腕がどのように動くか、一緒に思い出してみましょう。例えば、腕を曲げるとき、どの部分が動いているか覚えてる？\
そう、関節が動いていたよね。では、関節以外に動いている部分は何だったかな？そう、筋肉も動いているんだ。\
どうですか？もしわからないことがあれば、遠慮なく質問してくださいね。一度整理のために時間を取りますね。」"


def combine_pdf(directory):

    # ディレクトリ内のPDFファイルのリストを取得
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    pdf_files.sort()  # ファイル名でソート
    merger = PdfMerger()

    # PDFファイルが複数ある場合は結合
    if len(pdf_files) > 1:
        for filename in pdf_files:
            filepath = os.path.join(directory, filename)
            merger.append(filepath)

        # 結合したPDFを保存
        combined_pdf_path = os.path.join(directory, 'combined.pdf')
        with open(combined_pdf_path, 'wb') as out:
            merger.write(out)
        return combined_pdf_path
    elif len(pdf_files) == 1:
        # 一つのファイルの場合はそのままのパスを返す
        print("test="+os.path.join(directory, pdf_files[0]))
        return os.path.join(directory, pdf_files[0])
    else:
        print("dataファイルにPDFが存在しません")
        return None

def create_index():

    #index用のディレクトリ作成
    persist_dir = (os.path.dirname(__file__)+"\\").replace(os.getcwd().replace("C","c")+"\\","")
    index_dir = persist_dir+".\\index\\"
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    CJKPDFReader = download_loader("CJKPDFReader")#PDFローダーを準備
    loader=CJKPDFReader()

    #dataディレクトリ内の全てのPDFを結合してパスを取得する
    pdf_dir =combine_pdf(data_PATH)

    #rootを作業ディレクトリの相対パスに変換して読み込み↓　触るな！
    docs = loader.load_data(pdf_dir)
    index = GPTVectorStoreIndex.from_documents(docs)#docsからindex作成
    index.storage_context.persist(index_dir)#index保存

    # 結合したPDFファイルの削除
    # if pdf_dir and len(os.listdir(data_PATH)) > 1:
    #     print("消します！消します！消します！消します！消します！消します！消します！")
    #     os.remove(pdf_dir)
    return index

#インデックスから解答を生成する
def print_response(prompt: str, index):
    query_engine = index.as_query_engine()
    return query_engine.query(prompt+"日本語ください")


def generate_text(prompt, conversation_history):

    # プロンプトを会話履歴に追加
    conversation_history.append({"role": "user", "content": prompt})

    # GPT-4モデルを使用する場合
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history
    )
    message = ""

    for choice in response.choices:
        message += choice.message['content']

    # 応答文を会話履歴に追加
    conversation_history.append({"role": "assistant", "content": message})
    return message

def openjson(filename):
    # スクリプトのあるディレクトリを取得
    current_dir = os.path.dirname(__file__)
    # JSONファイルへの完全なパスを生成
    file_path = os.path.join(current_dir, "json", filename)
    with open(file_path, encoding='utf-8') as file:
        return json.load(file)
    
def JSONtoSpeech(jsonfilename,index):

    lesson_data=openjson(jsonfilename)
    for section in lesson_data:
        print(section['時間'])
        print(f"学習活動: {section['学習活動']}")
        print(f"指導上の留意点: {section['指導上の留意点']}")
        評価の観点 = section['評価の観点'] if section['評価の観点'] is not None else "なし"
        print(f"評価の観点: {評価の観点}")

        ans=print_response(operating+"学習活動:"+section["学習活動"]+"指導上の留意点:"+section["指導上の留意点"],index)
        section["教師の発話"] = ans
        print(section["教師の発話"])
        print("\n")  # セクション間に空行を挿入

    # 新しいJSONデータとして保存
    with open('json\\updated_lesson_plan.json', 'w', encoding='utf-8') as file:
        json.dump(lesson_data, file, ensure_ascii=False, indent=2)   
    print("処理終了です")


def main():
    # 会話履歴を格納するためのリストを初期化
    conversation_history = []

    #index作成
    index=create_index()    
    JSONtoSpeech("honji_tenkai.json",index)

if __name__ == "__main__":

    main()