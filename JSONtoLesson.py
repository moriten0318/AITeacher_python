import os
import openai
from dotenv import load_dotenv
import json

#GPT4.0に質問する簡単なScript

#APIキー取得して渡す
load_dotenv()
api_key = os.environ['OPENAI_API_KEY']
print(api_key)
openai.api_key=api_key

setting ="あなたは優秀な講師です。ブラックホールについて授業をする際にパワーポイントを作成します。\
    スライドごとに異なるセクションを用意します。これからあなたには授業のテーマとなるトピックを与えるので、どのようなセクションを用意するべきか、箇条書きで出力してください。"

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

if __name__ == "__main__":
    # 会話履歴を格納するためのリストを初期化
    conversation_history = []

    #設定を追加
    conversation_history.append({"role": "system", "content": setting})
    
    prompt ="ブラックホールについて教えて"

    print(openjson("honji.json"))

    # generated_text = generate_text(prompt, conversation_history)
    # print(generated_text)