import os
import openai
from dotenv import load_dotenv
import json


#ChatGPT4が生成したJSONファイルを読み込んで、教師の発話を追加できる

#APIキー取得して渡す
load_dotenv()
api_key = os.environ['OPENAI_API_KEY']
print(api_key)
openai.api_key=api_key


operating =\
"#あなたは小学校の教師です。\
#あなたに与えた「時間」、「学習活動」、「指導上の留意点」、「評価の観点」の項目を踏まえて、「そのセクションにおける教師の発話」を答えてください。\
#「学習活動」とは、授業内で生徒が達成するべき活動であり、教師の発話は学習活動が全て行えるように促すものになります。\
\
#出力する「教師の発話」とは、そのセクション内で行う学習活動や指導上の留意点の項目がすべて達成できるように、教師が生徒の前で話すような発言のことを指します。\
「教師の発話」では、教師は授業を聞いている生徒のことを意識し、常に生徒たちの学習状況を気にかける必要があります。\
例えば、「どうですか？理解できましたか？」「一度整理のために時間を取りますね。」などのように、時々教師が生徒に寄り添うような発言を入れてください。\
また、あなたは生徒に好かれる教師なので、ユーモアに富んだ語りをします。\
#教師の発話では口調を統一してください。以下の例で挙げている文章と同じ口調で話してください。\
#教師の発話以外の内容は発言しないでください。\
\
#以下は「教師の発話」の例です。\
「みなさん、こんにちは。今日も一緒に楽しく学んでいきましょうね。さて、前回の授業では、空気と水を注射器に閉じ込めてピストンを押すと、\
手ごたえはどう変わるかについて調べましたね。それぞれの結果がどう変わったか覚えていますか？\
そう、関節が動いていたよね。では、関節以外に動いている部分は何だったかな？そう、筋肉も動いているんだ。\
どうですか？もしわからないことがあれば、遠慮なく質問してくださいね。一度整理のために時間を取りますね。」"



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
    with open("json\\"+filename,encoding='utf-8') as file:
        return (json.load(file))
    
def speech_generate(jsonfilename,conversation_history):

    lesson_data=openjson(jsonfilename)

    for section in lesson_data:
        print(section['時間'])
        print(f"学習活動: {section['学習活動']}")
        print(f"指導上の留意点: {section['指導上の留意点']}")
        評価の観点 = section['評価の観点'] if section['評価の観点'] is not None else "なし"
        print(f"評価の観点: {評価の観点}")

        teacher_speech = generate_text("学習活動:"+section["学習活動"]+"指導上の留意点:"+section["指導上の留意点"],conversation_history)
        section["教師の発話"] = teacher_speech
        print("教師の発話"+section["教師の発話"])
        print("\n")  # セクション間に空行を挿入

    # 新しいJSONデータとして保存
    with open('json\\updated_lesson_plan.json', 'w', encoding='utf-8') as file:
        json.dump(lesson_data, file, ensure_ascii=False, indent=2)   
    print("処理終了です")


def main():
    # 会話履歴を格納するためのリストを初期化
    conversation_history = []
    #指示を追加
    conversation_history.append({"role": "system", "content": operating})

    speech_generate("honji_tenkai.json",conversation_history)

if __name__ == "__main__":

    main()